from dataclasses import dataclass
import random
import string

from flask import Flask, Response, jsonify, render_template, request
from flask_socketio import SocketIO, close_room, emit, join_room, leave_room  # type: ignore

from config.logging_config import build_logger
from other.computer_logic.basic import basic_choice
from other.scheduled.keep_alive import keep_alive
from play.web.client import BriscolaWeb

logger = build_logger(__name__)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")


SOCKET__OID: dict[str, str] = {}
""" A user's socket linked to their oid, which is the first localStorageId of the user. """

OID__ONLINE_ROOM: dict[str, str | None] = {}
""" The room each oid is currently in. """

OID__GAME: dict[str, BriscolaWeb | None] = {}  # the current game for each oid
""" The current game for each oid. """

ROOMS: dict[str, dict] = {}
""" Dictionary to store room information including room codes and players """


@dataclass
class OldOidInfo:
    """The user info to maintain after a user disconnects in case they reconnect later."""

    online_room: str | None = None
    game: BriscolaWeb | None = None


OLD_OID_INFO: dict[str, OldOidInfo] = {}
""" The info of a disconnected oid to reconnect them via localStorageId. """

# used to ping the keep-alive endpoint at some interval to avoid Render's 15min sleep
keep_alive()


def generate_room_code() -> str:
    """Generate a unique 4-digit numeric room code"""
    while True:
        code = "".join(random.choices(string.digits, k=4))
        if code not in ROOMS:
            return code


def create_room(room_code: str | None = None, player_count: int = 2) -> str:
    """Create a new room with a unique code"""
    if room_code is None:
        room_code = generate_room_code()

    ROOMS[room_code] = {
        "players": [],
        "created_at": str(request.headers.get("Date", "Unknown")),
        "game_active": False,
        "player_count": player_count,
    }
    return room_code


def cleanup_room(room_code: str) -> None:
    """Clean up a room and remove all players"""
    if room_code in ROOMS:
        # Remove all players from the room
        for oid in ROOMS[room_code]["players"]:
            if oid in OID__ONLINE_ROOM:
                del OID__ONLINE_ROOM[oid]
            if oid in OID__GAME:
                del OID__GAME[oid]

        # Close the room and delete it
        close_room(room_code)
        del ROOMS[room_code]
        logger.info(f"Room {room_code} cleaned up")


def force_players_out_of_room(room_code: str) -> None:
    """Force all players out of a room when game ends"""
    if room_code in ROOMS:
        players = ROOMS[room_code]["players"].copy()
        for oid in players:
            emit(
                "force_leave_room",
                {"message": "Game ended, returning to lobby"},
                to=oid if oid in SOCKET__OID.values() else None,
            )
        cleanup_room(room_code)


@app.route("/")
def index() -> str:
    return render_template("index.html")


@app.route("/turn")
def turn() -> str:
    return render_template("turn.html")


def get_oid(request_sid) -> str | None:
    return SOCKET__OID.get(request_sid, None)


def get_game_and_oid_from_request_sid(
    request_sid,
) -> tuple[str | None, BriscolaWeb | None]:
    oid = get_oid(request_sid)
    return oid, get_game_of_oid(oid)


@socketio.on("check_if_in_game")
def handle_check_if_in_game():
    oid = get_oid(request.sid) or request.sid
    emit("in_game_check_result", {"in_game": oid in OID__GAME})


@socketio.on("start_game")
def handle_start_game(data):
    game_mode = data.get("gameMode")
    difficulty = data.get("difficulty")
    player_count = int(data.get("playerCount", 2))
    room_code = data.get("room")  # Get room code if provided

    oid = get_oid(request.sid)
    online_room = room_code or get_online_room_of_oid(oid)
    room_oids = get_oids_in_online_room(online_room)

    if game_mode is None or difficulty is None:
        emit("error", {"message": "Missing data"})
        return

    difficulty = int(difficulty) // 1000

    try:
        if game_mode == "player":
            if online_room:
                if player_count not in [2, 4]:
                    emit(
                        "error",
                        {
                            "message": "Only 2 or 4-player online games are currently supported."
                        },
                    )
                    return

                if len(room_oids) == player_count:
                    # Initialize the game instance for this room
                    game = BriscolaWeb(online=True, player_count=player_count)
                    game.userid_playernum_map = {
                        user_id: player_num
                        for user_id, player_num in zip(
                            room_oids, range(len(game.players))
                        )
                    }

                    # Mark the room as having an active game
                    if online_room in ROOMS:
                        ROOMS[online_room]["game_active"] = True
                else:
                    emit(
                        "error",
                        {"message": "Not enough players to start the game."},
                    )
                    return
            else:
                game = BriscolaWeb(player_count=player_count)

        elif game_mode == "computer":
            # Set up a game against the computer with a specified difficulty
            game = BriscolaWeb(
                computer_count=1,
                computer_logic_override=(basic_choice,),
                computer_skill_level=difficulty,
                player_count=2,
            )
        else:
            emit("error", {"message": "Invalid gameMode"})
            return

        # if online room, set this as the game for every oid in the room
        if online_room:
            for oid in get_oids_in_online_room(online_room):
                OID__GAME[oid] = game

        # otherwise, set it just for the current oid who started the game
        else:
            OID__GAME[oid] = game

        in_room = online_room and game_mode == "player"
        emit_game_state(game, additional_data={"room": in_room})

    except Exception as e:
        emit("error", {"message": str(e)})


def emit_game_state(
    game: BriscolaWeb, continue_play: bool = False, additional_data: dict | None = None
) -> None:
    data = {"game_state": game.to_dict(), "continue_play": continue_play}
    if additional_data:
        data = data | additional_data

    target_room = "waiting_room" if game.online else False
    logger.info(
        f"Emitting game state to {'room waiting_room' if target_room else 'individual socket'}"
    )
    logger.info(f"Game state data: {data}")
    emit("game_state", data, to=target_room, include_self=True)


@socketio.on("get_state")
def handle_get_state(data=None):
    oid, oid_game = get_game_and_oid_from_request_sid(request_sid=request.sid)
    continue_play = data.get("continue_play") if data is not None else False

    emit_game_state(oid_game, continue_play=continue_play)


@socketio.on("play_active_card")
def handle_play_active_card(data):
    if data is None:
        emit("response", {"error": "Invalid request"})
        return

    card_idx = data.get("card_index")
    if card_idx is None:
        emit("response", {"error": "Missing card index"})
        return

    oid, game = get_game_and_oid_from_request_sid(request_sid=request.sid)
    logger.info(f"Player {oid} playing card at index {card_idx}")
    logger.info(f"Current game state before play: {game.to_dict()}")

    game.active_player_play_card_idx(card_idx=card_idx)
    logger.info(f"Game state after play: {game.to_dict()}")
    logger.info(f"Emitting active_card_played to socket {request.sid}")

    emit("active_card_played", game.to_dict(), to=request.sid)


@app.route("/api/get_computer_choice", methods=["POST"])
def get_computer_choice() -> tuple[Response, int]:
    if (oid := convert_request_to_oid(request)) == 1:
        return jsonify({"error": "OID not found"}), 404

    if (game := get_game_of_oid(oid)) is None:
        return jsonify({"error": "Game not found"}), 404

    computer_choice_idx = game.play_card_computer(cards=game.active_player.hand.cards)
    return jsonify({"card_idx": computer_choice_idx}), 200


@socketio.on("end_play")
def end_play():
    oid, game = get_game_and_oid_from_request_sid(request.sid)
    logger.info(f"Ending play for player {oid}")

    assert type(game) is BriscolaWeb

    game.end_play()
    logger.info(f"Game state after end_play: {game.to_dict()}")

    # send to online room if user is in one, otherwise just to the user's current socket
    target = get_online_room_of_oid(oid) or request.sid
    logger.info(f"Sending end_play event to target: {target}")

    emit("end_play", {"game_state": game.to_dict()}, to=target)


@socketio.on("end_game")
def end_game():
    oid, game = get_game_and_oid_from_request_sid(request.sid)

    if oid is None:
        return

    target = OID__ONLINE_ROOM.get(oid, request.sid)

    # return to /turn, and if the game isn't active at all it'll auto return home
    if not game or game.game_ongoing:
        emit("game_not_complete", to=target)
        return

    winner = next(
        (player for player in game.players if player.score > game.win_condition), None
    )

    if game.teams:
        winning_team = next(
            (team for team in game.teams if team.score > game.win_condition), None
        )
        if winning_team:
            message = f"Team {winning_team.name} wins!"
        else:
            max_team_score = max(team.score for team in game.teams)
            tied_teams = [
                team.name
                for team in game.teams
                if team.score == max_team_score and team.score >= 120
            ]
            if len(tied_teams) > 1:
                message = "The game ends in a tie!"
            else:
                message = f"Team {tied_teams[0]} wins!"

        sorted_teams = sorted(game.teams, key=lambda team: team.score, reverse=True)
        scores = [[f"Team {team.name}", f"{team.score}pts"] for team in sorted_teams]
    elif winner:
        message = f"{winner} wins!"
    else:
        max_score = max(player.score for player in game.players)
        tied_players = [
            str(player) for player in game.players if player.score == max_score
        ]
        if len(tied_players) > 1:
            message = "The game ends in a tie!"
        else:
            message = f"{tied_players[0]} wins!"

    sorted_players = sorted(game.players, key=lambda player: player.score, reverse=True)

    if not game.teams:
        scores = [[str(player), f"{player.score}pts"] for player in sorted_players]

    # Emit the winner message to the online room if one exists, or the user's current socket
    emit("end_game_response", {"message": message, "scores": scores}, to=target)

    # Clean up room if this was an online game
    online_room = get_online_room_of_oid(oid)
    if online_room and online_room in ROOMS:
        # Force all players out of the room after a delay
        socketio.start_background_task(
            lambda: socketio.sleep(5) or force_players_out_of_room(online_room)
        )


@app.route("/end_game")
def end_game_page():
    return render_template("end_game.html")


@socketio.on("disconnect")
def handle_disconnect():
    oid = get_oid(request.sid)
    online_room = get_online_room_of_oid(oid)
    game_of_oid = get_game_of_oid(oid)

    # store disconnected oid info in case they reconnect, we can get them back online via localStorageId
    if online_room or game_of_oid:
        OLD_OID_INFO[oid] = OldOidInfo(online_room=online_room, game=game_of_oid)

    # Check if we need to clean up room or end game
    if online_room in ROOMS and oid in ROOMS[online_room]["players"]:
        ROOMS[online_room]["players"].remove(oid)

        # If room is empty, clean it up
        if len(ROOMS[online_room]["players"]) == 0:
            cleanup_room(online_room)
        # If game is active and player disconnects, check if we need to end the game
        elif game_of_oid and game_of_oid.game_ongoing:
            remaining_players = [
                p for p in ROOMS[online_room]["players"] if p in OID__GAME
            ]
            if len(remaining_players) == 0:
                # End the game if no players remain
                logger.info(
                    f"All players left room {online_room}, ending game automatically"
                )
                game_of_oid.game_ongoing = False
                # Force remaining players out
                force_players_out_of_room(online_room)

    leave_room(room=online_room, sid=request.sid)
    send_room_user_count_update(online_room)

    if online_room:
        del OID__ONLINE_ROOM[oid]
    if game_of_oid:
        del OID__GAME[oid]

    if request.sid in SOCKET__OID:
        del SOCKET__OID[request.sid]

    print(
        f"User disconnected: {oid} on socket {request.sid}, Total users: {len(SOCKET__OID)}"
    )


def get_online_room_of_oid(oid: str | None) -> str | None:
    if oid is None:
        return None

    return OID__ONLINE_ROOM.get(oid, None)


def get_game_of_oid(oid: str | None) -> BriscolaWeb | None:
    if oid is None:
        return None

    return OID__GAME.get(oid, None)


@app.route("/api/get_waiting_room_users")
def get_waiting_room_users() -> tuple[Response, int]:
    # Get the room from the request
    room_code = request.args.get("room")

    if room_code and room_code in ROOMS:
        # Return users for a specific room
        oids = ROOMS[room_code]["players"]
        return jsonify({"users": oids, "room": room_code}), 200
    else:
        # Fallback to old behavior for backward compatibility
        oids = get_oids_in_online_room("waiting_room")
        if oids is None:
            oids = []
        return jsonify({"users": oids}), 200


def get_oids_in_online_room(room) -> list[str] | None:
    if room is None:
        return None

    # First check new room system
    if room in ROOMS:
        return ROOMS[room]["players"]

    # Fallback to old system for backward compatibility
    oids_in_room = set()
    for oid, room_of_oid in OID__ONLINE_ROOM.items():
        if room_of_oid == room:
            oids_in_room.update({oid})

    return list(oids_in_room)


@socketio.on("create_room")
def handle_create_room(data):
    """Create a new room with a unique code"""
    player_count = data.get("player_count", 2)
    room_code = create_room(player_count=player_count)
    oid = get_oid(request.sid)

    # Add player to the room
    ROOMS[room_code]["players"].append(oid)
    OID__ONLINE_ROOM[oid] = room_code
    join_room(room_code, sid=request.sid)

    emit("room_created", {"room_code": room_code, "player_count": player_count})
    logger.info(f"Room {room_code} created by player {oid} for {player_count} players")


@socketio.on("join_room_by_code")
def handle_join_room_by_code(data):
    """Join a room using a room code"""
    room_code = data.get("room_code", "").upper()
    oid = get_oid(request.sid)

    if not room_code:
        emit("error", {"message": "Room code is required"})
        return

    if room_code not in ROOMS:
        emit("error", {"message": "Room not found"})
        return

    if ROOMS[room_code]["game_active"]:
        emit("error", {"message": "Game already in progress"})
        return

    # Get the room's player count
    player_count = ROOMS[room_code].get("player_count", 2)
    current_players = len(ROOMS[room_code]["players"])

    # Check if room is full
    if current_players >= player_count:
        emit("error", {"message": "Room is full"})
        return

    # Add player to room
    if oid not in ROOMS[room_code]["players"]:
        ROOMS[room_code]["players"].append(oid)

    OID__ONLINE_ROOM[oid] = room_code
    join_room(room_code, sid=request.sid)

    emit("room_joined", {"room_code": room_code, "player_count": player_count})
    send_room_user_count_update(room_code)
    logger.info(f"Player {oid} joined room {room_code}")


@socketio.on("join_game")
def handle_join_game(data):
    room = data.get("room")
    oid = get_oid(request.sid)
    logger.info(f"Player {oid} joining room {room}")

    # add the current active socket to the room
    join_room(room, sid=request.sid)
    logger.info(f"Socket {request.sid} added to room {room}")

    # set room as the current room of the oid
    OID__ONLINE_ROOM[oid] = room
    logger.info(f"Current room mappings: {OID__ONLINE_ROOM}")

    send_room_user_count_update(room)


def send_room_user_count_update(room) -> None:
    users = get_oids_in_online_room(room) or []
    max_players = ROOMS[room].get("player_count", 2) if room in ROOMS else 2

    emit(
        "room_update",
        {
            "room": room,
            "users": users,
            "user_count": len(users),
            "max_players": max_players,
        },
        to=room,
    )


@socketio.on("leave_room")
def handle_leave_room(data):
    room = data.get("room")
    oid = get_oid(request.sid)
    game = get_game_of_oid(oid)

    # Remove from room data structure
    if room in ROOMS and oid in ROOMS[room]["players"]:
        ROOMS[room]["players"].remove(oid)

        # If room is empty, clean it up
        if len(ROOMS[room]["players"]) == 0:
            cleanup_room(room)
            return
        # If game is active and player leaves, check if we need to end the game
        elif game and game.game_ongoing:
            remaining_players = [p for p in ROOMS[room]["players"] if p in OID__GAME]
            if len(remaining_players) == 0:
                # End the game if no players remain
                logger.info(f"All players left room {room}, ending game automatically")
                game.game_ongoing = False
                # Force remaining players out
                force_players_out_of_room(room)
                return

    if oid in OID__ONLINE_ROOM:
        del OID__ONLINE_ROOM[oid]

    # Remove the game reference for this player
    if oid in OID__GAME:
        del OID__GAME[oid]

    leave_room(room, sid=request.sid)

    send_room_user_count_update(room)


@socketio.on("leave_game")
def handle_leave_game():
    oid = get_oid(request.sid)
    game = get_game_of_oid(oid)

    if not game:
        return

    online_room = get_online_room_of_oid(oid)

    # if user is in an online room
    if online_room:
        # Remove from room data structure
        if online_room in ROOMS and oid in ROOMS[online_room]["players"]:
            ROOMS[online_room]["players"].remove(oid)

            # If room is empty, clean it up
            if len(ROOMS[online_room]["players"]) == 0:
                cleanup_room(online_room)
            # If game is active and player leaves, check if we need to end the game
            elif game.game_ongoing:
                remaining_players = [
                    p for p in ROOMS[online_room]["players"] if p in OID__GAME
                ]
                if len(remaining_players) == 0:
                    # End the game if no players remain
                    logger.info(
                        f"All players left room {online_room}, ending game automatically"
                    )
                    game.game_ongoing = False
                    # Force remaining players out after a delay
                    socketio.start_background_task(
                        lambda: socketio.sleep(2)
                        or force_players_out_of_room(online_room)
                    )

        # If game has ended, leave the room
        if not game.game_ongoing:
            leave_room(online_room, sid=request.sid)

    # Clean up player data
    if oid in OID__ONLINE_ROOM:
        del OID__ONLINE_ROOM[oid]

    if oid in OID__GAME:
        del OID__GAME[oid]

    if oid in OLD_OID_INFO:
        del OLD_OID_INFO[oid]

    target = online_room or request.sid
    emit("room_closed", to=target)


def add_request_sid_to_sockets(request_sid: str, oid: str | None = None) -> None:
    if oid:
        # if there's a previous socket assigned to that oid, then delete the previous socket
        sockets_to_remove = [
            socket
            for socket, existing_oid in SOCKET__OID.items()
            if existing_oid == oid
        ]
        for socket in sockets_to_remove:
            del SOCKET__OID[socket]

        # set the new socket to be assigned to the old oid
        SOCKET__OID[request_sid] = oid
    else:
        SOCKET__OID[request_sid] = request_sid


@socketio.on("update_user_id")
def update_user_id(data):
    oid = data.get("user_id")
    add_request_sid_to_sockets(request_sid=request.sid, oid=oid)

    # if user's oid has old info, then reconnect them with their past state
    if (old_info := OLD_OID_INFO.get(oid, None)) is not None:
        OID__GAME[oid] = old_info.game
        OID__ONLINE_ROOM[oid] = old_info.online_room

        if old_info.online_room is not None:
            join_room(room=old_info.online_room, sid=request.sid)

    print(
        f"User connected: {oid} on socket {request.sid}, Total users: {len(SOCKET__OID)}"
    )

    return jsonify({"status": "success"}), 200


def convert_request_to_oid(req) -> str | None:
    request_data = req.get_json()

    socket_id = request_data.get("socket_id")
    return get_oid(socket_id)


@app.route("/api/convert_socketid_to_oid", methods=["POST"])
def convert_socketid_to_oid() -> tuple[Response, int]:
    return jsonify({"oid": convert_request_to_oid(request)}), 200


@app.route("/keep-alive")
def keep_app_alive():
    """Used to keep the server from sleeping on Render."""
    return "Keep-alive ping received", 200


@app.route("/api/get_available_rooms")
def get_available_rooms() -> tuple[Response, int]:
    """Get a list of available rooms that haven't started games yet"""
    available_rooms = []

    for room_code, room_data in ROOMS.items():
        if not room_data["game_active"]:
            player_count = len(room_data["players"])
            max_players = room_data.get("player_count", 2)
            if player_count < max_players:  # Room still has space
                available_rooms.append(
                    {
                        "room_code": room_code,
                        "player_count": player_count,
                        "max_players": max_players,
                    }
                )

    # Only return the 3 most recent rooms (or fewer if there aren't 3)
    available_rooms = available_rooms[:3]

    return jsonify({"rooms": available_rooms}), 200


if __name__ == "__main__":
    host = "127.0.0.1"
    port = 5000
    print(f"\n\n    🃏 Access the game at: http://{host}:{port} 🃏\n\n")
    socketio.run(
        app, host=host, port=port, debug=True, log_output=True, use_reloader=True
    )

import os
from dataclasses import dataclass

import sentry_sdk
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, render_template, request
from flask_socketio import SocketIO, close_room, emit, join_room, leave_room  # type: ignore

from config.logging_config import build_logger
from other.computer_logic.basic import basic_choice
from other.scheduled.keep_alive import keep_alive
from play.web.client import BriscolaWeb

sentry_sdk.init(
    dsn="https://a417850f811124c72be11a26ada21f55@o4507925862744064.ingest.de.sentry.io/4507925879849040",
    traces_sample_rate=1.0,  # capture 100% of issues for tracing
    profiles_sample_rate=1.0,  # profile 100% of sampled transactions
)


logger = build_logger(__name__)

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
socketio = SocketIO(app, cors_allowed_origins="*")


SOCKET__OID: dict[str, str] = {}
""" A user's socket linked to their oid, which is the first localStorageId of the user. """

OID__ONLINE_ROOM: dict[str, str | None] = {}
""" The room each oid is currently in. """

OID__GAME: dict[str, BriscolaWeb | None] = {}  # the current game for each oid
""" The current game for each oid. """


@dataclass
class OldOidInfo:
    """The user info to maintain after a user disconnects in case they reconnect later."""

    online_room: str | None = None
    game: BriscolaWeb | None = None


OLD_OID_INFO: dict[str, OldOidInfo] = {}
""" The info of a disconnected oid to reconnect them via localStorageId. """

# used to ping the keep-alive endpoint at some interval to avoid Render's 15min sleep
keep_alive()


@app.route("/turn")
def turn() -> str:
    return render_template("turn.html")


def get_oid(request_sid) -> str | None:
    return SOCKET__OID.get(request_sid, None)


def get_game_and_oid_from_request_sid(request_sid) -> tuple[str | None, BriscolaWeb | None]:
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

    oid = get_oid(request.sid)
    online_room = get_online_room_of_oid(oid)
    room_oids = get_oids_in_online_room(online_room)

    if game_mode is None or difficulty is None:
        emit("error", {"message": "Missing data"})
        return

    difficulty = int(difficulty) // 1000

    try:
        if game_mode == "player":
            if online_room:
                if len(room_oids) == 2:
                    # Initialize the game instance for this room
                    game = BriscolaWeb(online=True)
                    game.userid_playernum_map = {
                        user_id: player_num
                        for user_id, player_num in zip(room_oids, range(len(game.players)))
                    }
                else:
                    emit(
                        "error",
                        {"message": "Not enough players to start the game."},
                    )
                    return
            else:
                game = BriscolaWeb()

        elif game_mode == "computer":
            # Set up a game against the computer with a specified difficulty
            game = BriscolaWeb(
                computer_count=1,
                computer_logic_override=(basic_choice,),
                computer_skill_level=difficulty,
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

    emit("game_state", data, to="public_room" if game.online else False, include_self=True)


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

    game.active_player_play_card_idx(card_idx=card_idx)

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

    assert type(game) is BriscolaWeb

    game.end_play()

    # send to online room if user is in one, otherwise just to the user's current socket
    target = get_online_room_of_oid(oid) or request.sid

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

    max_score = max(player.score for player in game.players)
    winner = next((player for player in game.players if player.score > game.win_condition), None)

    if winner:
        message = f"{winner} wins!"
    else:
        tied_players = [str(player) for player in game.players if player.score == max_score]
        if len(tied_players) > 1:
            message = "The game ends in a tie!"
        else:
            message = f"{tied_players[0]} wins!"

    sorted_players = sorted(game.players, key=lambda player: player.score, reverse=True)

    # must use \r\n for line break to work in textContent attribute of html
    scores = [[str(player), f"{player.score}pts"] for player in sorted_players]

    # Emit the winner message to the online room if one exists, or the user's current socket
    emit("end_game_response", {"message": message, "scores": scores}, to=target)


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

    leave_room(room=online_room, sid=request.sid)
    send_room_user_count_update(online_room)

    if online_room:
        del OID__ONLINE_ROOM[oid]
    if game_of_oid:
        del OID__GAME[oid]

    if request.sid in SOCKET__OID:
        del SOCKET__OID[request.sid]

    print(f"User disconnected: {oid} on socket {request.sid}, Total users: {len(SOCKET__OID)}")


def get_online_room_of_oid(oid: str | None) -> str | None:
    if oid is None:
        return None

    return OID__ONLINE_ROOM.get(oid, None)


def get_game_of_oid(oid: str | None) -> BriscolaWeb | None:
    if oid is None:
        return None

    return OID__GAME.get(oid, None)


@app.route("/api/get_room_users", methods=["GET"])
def get_room_users() -> tuple[Response, int]:
    room = request.args.get("room")
    oids = get_oids_in_online_room(room)
    if oids is None:
        return jsonify({"error": "Room or users not found"}), 404
    return jsonify({"users": oids}), 200


def get_oids_in_online_room(room) -> list[str] | None:
    if room is None:
        return None

    oids_in_room = set()
    for oid, room_of_oid in OID__ONLINE_ROOM.items():
        if room_of_oid == room:
            oids_in_room.update({oid})
    return list(oids_in_room)


@socketio.on("join_game")
def handle_join_game(data):
    room = data.get("room")
    oid = get_oid(request.sid)

    # add the current active socket to the room
    join_room(room, sid=request.sid)

    # set room as the current room of the oid
    OID__ONLINE_ROOM[oid] = room

    send_room_user_count_update(room)


def send_room_user_count_update(room) -> None:
    emit("room_update", {"room": room, "users": get_oids_in_online_room(room)}, broadcast=True)


@socketio.on("leave_room")
def handle_leave_room(data):
    room = data.get("room")
    oid = get_oid(request.sid)

    if oid in OID__ONLINE_ROOM:
        del OID__ONLINE_ROOM[oid]

    leave_room(room, sid=request.sid)

    send_room_user_count_update(room)


@socketio.on("leave_game")
def handle_leave_game():
    oid = get_oid(request.sid)
    game = get_game_of_oid(oid)

    # if user is in an online room and the game has ended
    if (online_room := get_online_room_of_oid(oid)) and not game.game_ongoing:
        leave_room(online_room, sid=request.sid)
        close_room(online_room)

    if oid in OID__ONLINE_ROOM or oid in OID__GAME:
        if not game.game_ongoing:
            del OLD_OID_INFO[oid]

        if oid in OID__ONLINE_ROOM:
            del OID__ONLINE_ROOM[oid]

        if oid in OID__GAME:
            del OID__GAME[oid]

    target = online_room or request.sid

    emit("room_closed", to=target)


def add_request_sid_to_sockets(request_sid: str, oid: str | None = None) -> None:
    if oid:
        # if there's a previous socket assigned to that oid, then delete the previous socket
        sockets_to_remove = [
            socket for socket, existing_oid in SOCKET__OID.items() if existing_oid == oid
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

    print(f"User connected: {oid} on socket {request.sid}, Total users: {len(SOCKET__OID)}")

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


if __name__ == "__main__":
    socketio.run(app, debug=True, log_output=True, use_reloader=True)

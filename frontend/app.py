from flask import Flask, Response, jsonify, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room  # type: ignore

from config.logging_config import build_logger
from frontend.services.game_service import game_service
from frontend.services.room_service import room_service
from frontend.services.socket_service import socket_service
from frontend.services.user_service import user_service
from frontend.types import (
    EmitType,
    ErrorKeys,
    CardPlayedKeys,
    GameStateKeys,
    RoomCreateJoinKeys,
)
from other.scheduled.keep_alive import keep_alive

logger = build_logger(__name__)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Keep alive for Render.com
keep_alive()


@app.route("/")
def index() -> str:
    return render_template("index.html")


@app.route("/turn")
def turn() -> str:
    return render_template("turn.html")


@app.route("/end_game")
def end_game_page():
    return render_template("end_game.html")


@socketio.on("check_if_in_game")
def handle_check_if_in_game():
    socket_service.handle_check_if_in_game()


@socketio.on("start_game")
def handle_start_game(data):
    game_mode = data.get("game_mode")
    username = data.get("username")

    # Get the user's OID
    oid = socket_service.get_oid(request.sid)
    if not oid:
        emit(EmitType.ERROR, {ErrorKeys.MESSAGE: "User ID not found"})
        return

    # For online games, username is required
    if game_mode == "online" and not username:
        emit(
            EmitType.ERROR, {ErrorKeys.MESSAGE: "Username is required for online games"}
        )
        return

    # If username is provided, save it
    if username:
        user_service.set_username(oid, username)

    # Continue with game creation
    socket_service.handle_start_game(data)


@socketio.on("get_state")
def handle_get_state(data=None):
    oid, oid_game = socket_service.get_game_and_oid_from_request_sid(
        request_sid=request.sid
    )

    if oid_game is None:
        logger.error(f"No game found for OID: {oid}, Socket: {request.sid}")
        logger.error(f"Current oid_to_game mappings: {user_service.oid_to_game.keys()}")
        logger.error(f"Current socket_to_oid mappings: {user_service.socket_to_oid}")
        logger.error(f"Saved sessions: {user_service.saved_sessions.keys()}")
        emit(
            EmitType.ERROR,
            {ErrorKeys.MESSAGE: "Game not found. Please start a new game."},
        )
        return

    continue_play = data.get("continue_play") if data is not None else False
    game_service.emit_game_state(oid_game, continue_play=continue_play)


@socketio.on("play_active_card")
def handle_play_active_card(data):
    if data is None:
        emit(EmitType.ERROR, {ErrorKeys.MESSAGE: "Invalid request"})
        return

    card_idx = data.get(CardPlayedKeys.CARD_INDEX)
    if card_idx is None:
        emit(EmitType.ERROR, {ErrorKeys.MESSAGE: "Missing card index"})
        return

    oid, game = socket_service.get_game_and_oid_from_request_sid(
        request_sid=request.sid
    )
    logger.info(f"Player {oid} playing card at index {card_idx}")
    logger.info(f"Current game state before play: {game.to_dict()}")

    game_state = game_service.handle_player_card_play(game, card_idx)
    logger.info(f"Game state after play: {game_state}")
    logger.info(f"Emitting active_card_played to socket {request.sid}")

    emit(EmitType.ACTIVE_CARD_PLAYED, game_state, to=request.sid)


@app.route("/api/get_computer_choice", methods=["POST"])
def get_computer_choice() -> tuple[Response, int]:
    request_data = request.get_json()
    socket_id = request_data.get("socket_id")
    oid = socket_service.get_oid(socket_id)

    if oid is None:
        return jsonify({"error": "OID not found"}), 404

    if (game := socket_service.get_game_of_oid(oid)) is None:
        return jsonify({"error": "Game not found"}), 404

    computer_choice_idx = game.play_card_computer(cards=game.active_player.hand.cards)
    return jsonify({"card_idx": computer_choice_idx}), 200


@socketio.on("end_play")
def handle_end_play():
    oid, game = socket_service.get_game_and_oid_from_request_sid(request.sid)
    logger.info(f"Ending play for player {oid}")

    assert game is not None
    game.end_play()
    logger.info(f"Game state after end_play: {game.to_dict()}")

    # send to online room if user is in one, otherwise just to the user's current socket
    target = socket_service.get_online_room_of_oid(oid) or request.sid
    logger.info(f"Sending end_play event to target: {target}")

    emit(EmitType.END_PLAY, {GameStateKeys.GAME_STATE: game.to_dict()}, to=target)


@socketio.on("end_game")
def handle_end_game():
    oid, game = socket_service.get_game_and_oid_from_request_sid(
        request_sid=request.sid
    )
    online_room = socket_service.get_online_room_of_oid(oid)

    if oid is None or game is None:
        emit(EmitType.ERROR, {ErrorKeys.MESSAGE: "Game not found"})
        return

    if online_room:
        # Force all players to leave and clean up the room
        room_service.force_players_out_of_room(
            online_room, socket_service.socket_to_oid
        )
        room_service.cleanup_room(
            online_room,
            oid_online_room=user_service.oid_to_room,
            oid_game=user_service.oid_to_game,
        )
        game_service.notify_end_game(game, target=online_room)
    else:
        # In local mode, just notify the current user
        game_service.notify_end_game(game, target=request.sid)

    # Clear the game
    if oid and oid in user_service.oid_to_game:
        del user_service.oid_to_game[oid]


@socketio.on("disconnect")
def handle_disconnect():
    socket_service.handle_disconnect()


@app.route("/api/get_waiting_room_users")
def get_waiting_room_users() -> tuple[Response, int]:
    # Get the room from the request
    room_code = request.args.get("room")

    if room_code and room_code in room_service.rooms:
        # Return users for a specific room
        oids = room_service.rooms[room_code]["players"]
        return jsonify({"users": oids, "room": room_code}), 200
    else:
        # No room specified or invalid room
        return jsonify({"users": [], "error": "Room not specified or invalid"}), 200


@socketio.on("create_room")
def handle_create_room(data):
    player_count = data.get("player_count", 2)
    username = data.get("username")

    # Get the user's OID
    oid = socket_service.get_oid(request.sid)
    if not oid:
        emit(EmitType.ERROR, {ErrorKeys.MESSAGE: "User ID not found"})
        return

    # If username is provided, save it
    if username:
        user_service.set_username(oid, username)
        logger.info(f"User {oid} ({username}) is creating a room")

    # Create a new room
    room_code = room_service.create_room(player_count=player_count)

    # Add the creator to the room
    room_service.add_user_to_room(oid, room_code)

    # Join the socket.io room
    join_room(room_code)

    # Set the user's current room
    user_service.set_room(oid, room_code)

    # Get current room data
    room_data = room_service.get_room_data(room_code)
    emit("room_joined", room_data)


@socketio.on("join_room_by_code")
def handle_join_room_by_code(data):
    room_code = data.get(RoomCreateJoinKeys.ROOM_CODE)
    username = data.get("username")

    # Require username
    if not username:
        emit(EmitType.ERROR, {ErrorKeys.MESSAGE: "Username is required to join a room"})
        return

    # Validate room code
    if not room_code or not isinstance(room_code, str):
        emit(EmitType.ERROR, {ErrorKeys.MESSAGE: "Invalid room code"})
        return

    # Convert to uppercase
    room_code = room_code.upper()

    # Check if the room exists
    if room_code not in room_service.rooms:
        emit(EmitType.ERROR, {ErrorKeys.MESSAGE: "Room not found"})
        return

    # Check if game is already active
    if room_service.rooms[room_code]["game_active"]:
        emit(EmitType.ERROR, {ErrorKeys.MESSAGE: "Game already in progress"})
        return

    # Get user ID
    oid = socket_service.get_oid(request.sid)
    if not oid:
        emit(EmitType.ERROR, {ErrorKeys.MESSAGE: "User ID not found"})
        return

    # Save username
    user_service.set_username(oid, username)
    logger.info(f"User {oid} ({username}) is joining room {room_code}")

    # Add user to the room
    success = room_service.add_user_to_room(oid, room_code)
    if not success:
        emit(EmitType.ERROR, {ErrorKeys.MESSAGE: "Failed to join room"})
        return

    # Join the socket.io room
    join_room(room_code)

    # Set the user's current room
    user_service.set_room(oid, room_code)

    # Get current room data
    room_data = room_service.get_room_data(room_code)
    emit("room_joined", room_data)


@socketio.on("select_team")
def handle_select_team(data):
    team = data.get("team")
    room = data.get("room")
    oid = socket_service.get_oid(request.sid)

    if not room or not team or not oid:
        emit(EmitType.ERROR, {ErrorKeys.MESSAGE: "Missing data for team selection"})
        return

    # Store the team selection for this user
    if not hasattr(user_service, "user_teams"):
        user_service.user_teams = {}

    user_service.user_teams[oid] = team
    logger.info(f"Player {oid} selected team {team} in room {room}")

    # Notify other room members about the team selection
    room_service.send_team_update(room, oid, team)


@socketio.on("join_game")
def handle_join_game(data):
    room = data.get("room")
    oid = socket_service.get_oid(request.sid)
    logger.info(f"Player {oid} joining room {room}")

    # add the current active socket to the room
    join_room(room, sid=request.sid)
    logger.info(f"Socket {request.sid} added to room {room}")

    # set room as the current room of the oid
    user_service.set_room(oid, room)
    logger.info(f"Current room mappings: {user_service.oid_to_room}")

    room_service.send_room_update(room, socket_service.get_oids_in_room)


@socketio.on("leave_room")
def handle_leave_room(data):
    room = data.get("room")
    oid = socket_service.get_oid(request.sid)
    game = socket_service.get_game_of_oid(oid)

    # Remove from room data structure
    if room in room_service.rooms and oid in room_service.rooms[room]["players"]:
        room_service.rooms[room]["players"].remove(oid)

        # If room is empty, clean it up
        if len(room_service.rooms[room]["players"]) == 0:
            room_service.cleanup_room(
                room, user_service.oid_to_room, user_service.oid_to_game
            )
            return
        # If game is active and player leaves, check if we need to end the game
        elif game and game.game_ongoing:
            remaining_players = [
                p
                for p in room_service.rooms[room]["players"]
                if p in user_service.oid_to_game
            ]
            if len(remaining_players) == 0:
                # End the game if no players remain
                logger.info(f"All players left room {room}, ending game automatically")
                game.game_ongoing = False
                # Force remaining players out
                room_service.force_players_out_of_room(room, user_service.socket_to_oid)
                return

    if oid in user_service.oid_to_room:
        del user_service.oid_to_room[oid]

    # Remove the game reference for this player
    if oid in user_service.oid_to_game:
        del user_service.oid_to_game[oid]

    leave_room(room, sid=request.sid)

    room_service.send_room_update(room, socket_service.get_oids_in_room)


@socketio.on("leave_game")
def handle_leave_game():
    oid = socket_service.get_oid(request.sid)
    game = socket_service.get_game_of_oid(oid)

    if not game:
        return

    online_room = socket_service.get_online_room_of_oid(oid)

    # if user is in an online room
    if online_room:
        # Remove from room data structure
        if (
            online_room in room_service.rooms
            and oid in room_service.rooms[online_room]["players"]
        ):
            room_service.rooms[online_room]["players"].remove(oid)

            # If room is empty, clean it up
            if len(room_service.rooms[online_room]["players"]) == 0:
                room_service.cleanup_room(
                    online_room, user_service.oid_to_room, user_service.oid_to_game
                )
            # If game is active and player leaves, check if we need to end the game
            elif game.game_ongoing:
                remaining_players = [
                    p
                    for p in room_service.rooms[online_room]["players"]
                    if p in user_service.oid_to_game
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
                        or room_service.force_players_out_of_room(
                            online_room, user_service.socket_to_oid
                        )
                    )

        # If game has ended, leave the room
        if not game.game_ongoing:
            leave_room(online_room, sid=request.sid)

    # Clean up player data
    user_service.remove_user(oid)

    target = online_room or request.sid
    emit(EmitType.ROOM_CLOSED, to=target)


@socketio.on("update_user_id")
def update_user_id(data):
    oid = data.get("user_id")
    username = data.get("username")

    # Register this socket with the user ID
    user_service.register_socket(request.sid, oid)

    # Store username if provided
    if username:
        user_service.set_username(oid, username)

    # Try to restore a saved session if one exists
    restored = user_service.restore_session(request.sid, oid)

    logger.info(
        f"User connected: {oid} on socket {request.sid}, Username: {username}, Total users: {user_service.get_socket_count()}, Session restored: {restored}"
    )

    return jsonify({"status": "success"}), 200


@app.route("/api/convert_socketid_to_oid", methods=["POST"])
def convert_socketid_to_oid() -> tuple[Response, int]:
    request_data = request.get_json()
    socket_id = request_data.get("socket_id")
    return jsonify({"oid": user_service.get_oid_from_socket(socket_id)}), 200


@app.route("/keep-alive")
def keep_app_alive():
    """Used to keep the server from sleeping on Render."""
    return "Keep-alive ping received", 200


@app.route("/api/get_available_rooms")
def get_available_rooms() -> tuple[Response, int]:
    """Get a list of available rooms that haven't started games yet"""
    available_rooms = []

    for room_code, room_data in room_service.rooms.items():
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

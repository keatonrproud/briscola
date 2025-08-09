from flask import Flask, Response, jsonify, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room  # type: ignore

from config.logging_config import build_logger
from frontend.services.game_service import emit_game_state
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
    socket_service.handle_start_game(data)


@socketio.on("get_state")
def handle_get_state(data=None):
    oid, oid_game = socket_service.get_game_and_oid_from_request_sid(
        request_sid=request.sid
    )
    continue_play = data.get("continue_play") if data is not None else False
    emit_game_state(oid_game, continue_play=continue_play)


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

    game.active_player_play_card_idx(card_idx=card_idx)
    logger.info(f"Game state after play: {game.to_dict()}")
    logger.info(f"Emitting active_card_played to socket {request.sid}")

    emit(EmitType.ACTIVE_CARD_PLAYED, game.to_dict(), to=request.sid)


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
    from frontend.services.game_service import notify_end_game

    oid, game = socket_service.get_game_and_oid_from_request_sid(request.sid)

    if oid is None:
        return

    target = user_service.get_room(oid) or request.sid

    # return to /turn, and if the game isn't active at all it'll auto return home
    if not game or game.game_ongoing:
        emit(EmitType.GAME_NOT_COMPLETE, to=target)
        return

    # Notify players about end game
    notify_end_game(game, target)

    # Clean up room if this was an online game
    online_room = socket_service.get_online_room_of_oid(oid)
    if online_room and online_room in room_service.rooms:
        # Force all players out of the room after a delay
        socketio.start_background_task(
            lambda: socketio.sleep(5)
            or room_service.force_players_out_of_room(
                online_room, user_service.socket_to_oid
            )
        )


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
        # Fallback to old behavior for backward compatibility
        oids = room_service.get_oids_in_room("waiting_room")
        if oids is None:
            oids = []
        return jsonify({"users": oids}), 200


@socketio.on("create_room")
def handle_create_room(data):
    socket_service.handle_create_room(data)


@socketio.on("join_room_by_code")
def handle_join_room_by_code(data):
    """Join a room using a room code"""
    room_code = data.get("room_code", "").upper()
    oid = socket_service.get_oid(request.sid)

    if not room_code:
        emit(EmitType.ERROR, {ErrorKeys.MESSAGE: "Room code is required"})
        return

    if room_code not in room_service.rooms:
        emit(EmitType.ERROR, {ErrorKeys.MESSAGE: "Room not found"})
        return

    if room_service.rooms[room_code]["game_active"]:
        emit(EmitType.ERROR, {ErrorKeys.MESSAGE: "Game already in progress"})
        return

    # Get the room's player count
    max_players = room_service.rooms[room_code].get("player_count", 2)
    current_players = len(room_service.rooms[room_code]["players"])

    # Check if room is full
    if current_players >= max_players:
        emit(EmitType.ERROR, {ErrorKeys.MESSAGE: "Room is full"})
        return

    # Add player to room
    if oid not in room_service.rooms[room_code]["players"]:
        room_service.rooms[room_code]["players"].append(oid)
        # Update current_players after adding this player
        current_players = len(room_service.rooms[room_code]["players"])

    user_service.set_room(oid, room_code)
    join_room(room_code, sid=request.sid)

    emit(
        EmitType.ROOM_JOINED,
        {
            RoomCreateJoinKeys.ROOM_CODE: room_code,
            RoomCreateJoinKeys.PLAYER_COUNT: current_players,
            RoomCreateJoinKeys.MAX_PLAYERS: max_players,
        },
    )
    room_service.send_room_update(room_code, socket_service.get_oids_in_room)
    logger.info(f"Player {oid} joined room {room_code}")


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

    # Register this socket with the user ID
    user_service.register_socket(request.sid, oid)

    # Try to restore a saved session if one exists
    restored = user_service.restore_session(request.sid, oid)

    logger.info(
        f"User connected: {oid} on socket {request.sid}, Total users: {user_service.get_socket_count()}, Session restored: {restored}"
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

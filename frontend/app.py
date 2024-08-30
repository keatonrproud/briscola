import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from flask_socketio import SocketIO, emit, join_room, leave_room, close_room

from backend.computer_logic.basic import basic_choice
from config.logging_config import build_logger
from play.web.client import BriscolaWeb

logger = build_logger(__name__)

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
socketio = SocketIO(app, cors_allowed_origins="*")  # Use proper CORS settings in production

game = BriscolaWeb(computer_count=1, computer_logic_override=(basic_choice,))

# Store connections and rooms
USER_GAME_ROOM: dict[str, str] = {}  # {user_id: room_name}
OLD_USER_GAME_ROOM: dict[str, str] = (
    {}
)  # {user_id: room_name}    used to retain room membership after disconnect
ROOM_USERS: dict[str, set[str]] = {"public_room": set()}  # {room_name: {user_ids}}
ROOM_ONLINE_GAME: dict[str, BriscolaWeb] = {}  # {room_name: game_instance}
USER_LOCAL_GAME: dict[str, BriscolaWeb] = {}  # {user_id: game_instance}
USER_SOCKET: dict[str, str | None] = {}  # {user_string: current_socket_string}


@app.route("/")
def index() -> str:
    return render_template("index.html")


@app.route("/turn")
def turn() -> str:
    return render_template("turn.html")

def get_oid(request_sid) -> str:
    return USER_SOCKET.get(request_sid, None)


@socketio.on("check_if_in_game")
def handle_check_if_in_game():
    oid = get_oid(request.sid) or request.sid

    in_game = USER_GAME_ROOM.get(oid, None) is not None or oid in USER_LOCAL_GAME or request.sid in USER_LOCAL_GAME

    emit("in_game_check_result", {"in_game": in_game})

def get_game_from_oid(oid) -> BriscolaWeb:
    if oid in USER_LOCAL_GAME:
        game = USER_LOCAL_GAME[oid]
    else:
        room = USER_GAME_ROOM[oid]

        # if the user is playing in a muliplayer room
        if room:
            game = ROOM_ONLINE_GAME[room]
        else:
            game = USER_LOCAL_GAME[oid]

    return game


def get_game_and_oid_from_request_sid(request_sid) -> tuple[str, BriscolaWeb]:
    oid = get_oid(request_sid)
    return oid, get_game_from_oid(oid)


@socketio.on("start_game")
def handle_start_game(data):
    game_mode = data.get("gameMode")
    difficulty = data.get("difficulty")
    oid = get_oid(request.sid)
    room = USER_GAME_ROOM.get(oid, None)

    if game_mode is None or difficulty is None:
        emit("error", {"message": "Missing data"})
        return

    difficulty = int(difficulty) // 1000

    try:
        if game_mode == "player":
            if room and len(ROOM_USERS[room]) == 2:
                if room in ROOM_USERS and len(ROOM_USERS[room]) == 2:
                    # Initialize the game instance for this room
                    room_game = ROOM_ONLINE_GAME[room] = BriscolaWeb(fixed_shown_player=True)
                    room_game.userid_playernum_map = {
                        user_id: player_num
                        for user_id, player_num in zip(
                            ROOM_USERS[room], range(len(room_game.players))
                        )
                    }
                    in_room = True
                else:
                    emit(
                        "error",
                        {"message": "Not enough players to start the game."},
                    )
                    return
            else:
                room_game = USER_LOCAL_GAME[oid] = BriscolaWeb()
                in_room = False

        elif game_mode == "computer":
            # Set up a game against the computer with a specified difficulty
            room_game = USER_LOCAL_GAME[oid] = BriscolaWeb(
                computer_count=1,
                computer_logic_override=(basic_choice,),
                computer_skill_level=difficulty,
            )
            in_room = False
        else:
            emit("error", {"message": "Invalid gameMode"})
            return

        emit_game_state(room_game, additional_data={"room": in_room})

    except Exception as e:
        emit("error", {"message": str(e)})


def emit_game_state(
    game: BriscolaWeb, continue_play: bool = False, additional_data: dict = dict()
) -> None:
    emit(
        "game_state",
        {"game_state": game.to_dict(), "continue_play": continue_play} | additional_data,
        to="public_room" if game.fixed_shown_player else False,
        include_self=True,
    )


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

    emit("active_card_played", game.to_dict(), room=request.sid)


@app.route("/api/get_computer_choice", methods=["GET"])
def get_computer_choice() -> jsonify:
    return jsonify({"card_idx": game.play_card_computer(cards=game.active_player.hand.cards)})


@socketio.on("end_play")
def end_play() -> None:
    oid, game = get_game_and_oid_from_request_sid(request.sid)
    room = USER_GAME_ROOM[oid]

    game.end_play()

    emit("end_play", {"game_state": game.to_dict()}, room=room)


@socketio.on('end_game')
def end_game():
    oid, game = get_game_and_oid_from_request_sid(request.sid)

    online_room = USER_GAME_ROOM.get(oid, None)
    user = request.sid

    target = online_room or user

    max_score = max(player.score for player in game.players)
    winner = next((player for player in game.players if player.score > game.win_condition), None)

    if winner:
        winner_message = f"{winner} wins with {winner.score} points!"
    else:
        tied_players = [str(player) for player in game.players if player.score == max_score]
        if len(tied_players) > 1:
            winner_message = f"The game ends in a tie with {' and '.join(tied_players)} having {max_score} points!"
        else:
            winner_message = f"{tied_players[0]} wins with {max_score} points!"

    # Emit the winner message to all clients
    emit('end_game_response', {'winner_message': winner_message}, to=target)

@app.route('/end_game')
def end_game_page():
    return render_template("end_game.html")


def add_user_to_room(oid, room) -> None:
    if room not in ROOM_USERS:
        ROOM_USERS[room] = set()

    USER_GAME_ROOM[oid] = room
    ROOM_USERS[room] = ROOM_USERS[room] | {oid}


@socketio.on("connect")
def handle_connect():
    """The first time a user connects, they're assigned their 'permanent' oid as their first socket.id"""
    user_id = request.sid

    USER_GAME_ROOM[user_id] = None
    USER_SOCKET[user_id] = user_id

    emit("update_user_count", {"count": len(USER_GAME_ROOM.keys())}, broadcast=True)
    print(f"User connected: {user_id}, Total users: {len(USER_GAME_ROOM.keys())}")


@socketio.on("disconnect")
def handle_disconnect():
    oid = get_oid(request.sid)
    OLD_USER_GAME_ROOM[oid] = USER_GAME_ROOM[oid]
    room = USER_GAME_ROOM.pop(oid, None)

    if room and room in ROOM_USERS:
        ROOM_USERS[room].remove(oid)
        leave_room(room)
        emit("room_update", {"room": room, "users": list(ROOM_USERS[room])}, broadcast=True)


@app.route("/api/get_room_users", methods=["GET"])
def get_room_users():
    room = request.args.get("room")
    if room in ROOM_USERS:
        return jsonify({"users": list(ROOM_USERS[room])})
    return jsonify({"error": "Room not found"}), 404


@socketio.on("join_game")
def handle_join_game(data):
    room = data.get("room")
    oid = get_oid(request.sid)

    join_room(room, sid=request.sid)
    add_user_to_room(oid, room)

    emit("room_update", {"room": room, "users": list(ROOM_USERS[room])}, broadcast=True)


def remove_user_from_room(user_id, room) -> None:
    ROOM_USERS[room].remove(user_id)
    if user_id in USER_GAME_ROOM:
        del USER_GAME_ROOM[user_id]

    print("remove_user_from_room", USER_GAME_ROOM)


@socketio.on("leave_room")
def handle_leave_room(data):
    room = data.get("room")
    oid = get_oid(request.sid)

    leave_room(room, sid=oid)

    if room:
        remove_user_from_room(oid, room)

    emit("room_update", {"room": room, "users": list(ROOM_USERS[room])}, broadcast=True)


@socketio.on("leave_game")
def handle_leave_game():
    oid = get_oid(request.sid)

    # if user is in an online room
    if room := USER_GAME_ROOM.get(oid, None):
        emit("room_closed", to=room)
        close_room(room)
    else:
        emit("room_closed", to=request.sid)

@socketio.on("update_user_id")
def update_user_id(data):
    old_id = data.get("user_id")
    new_id = request.sid

    if new_id in USER_SOCKET.keys():
        USER_SOCKET[new_id] = USER_SOCKET[old_id]
        del USER_SOCKET[old_id]

    if old_id in OLD_USER_GAME_ROOM.keys():
        USER_GAME_ROOM[old_id] = OLD_USER_GAME_ROOM[old_id]
        join_room(room=OLD_USER_GAME_ROOM[old_id], sid=new_id)
        if new_id in USER_GAME_ROOM:
            del USER_GAME_ROOM[new_id]

    return jsonify({"status": "success"})


@app.route("/api/convert_socketid_to_oid", methods=["POST"])
def convert_socketid_to_oid():
    data = request.get_json()

    if not data or "socket_id" not in data:
        return jsonify({"error": "Invalid input"}), 400

    socket_id = data.get("socket_id")
    oid = get_oid(socket_id)

    if oid is None:
        return jsonify({"error": "OID not found"}), 404

    return jsonify({"oid": get_oid(socket_id)})


if __name__ == "__main__":
    socketio.run(app, debug=True)

import json
import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room

from backend.computer_logic.basic import basic_choice
from play_web.web_client import BriscolaWeb

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
socketio = SocketIO(app, cors_allowed_origins="*")  # Use proper CORS settings in production

game = BriscolaWeb(computer_count=1, computer_logic_override=(basic_choice,))

# Store connections and rooms
USER_ROOM: dict[str, str] = {}  # {user_id: room_name}
ROOM_USERS: dict[str, set[str]] = {"public_room": set()}  # {room_name: {user_ids}}
ROOM_GAME: dict[str, BriscolaWeb] = {}  # {room_name: game_instance}


@app.route("/")
def index() -> str:
    return render_template("index.html")


@app.route("/turn")
def turn() -> str:
    return render_template("turn.html")


@socketio.on("reset_state")
def reset_state(data):
    game_mode = data.get("gameMode")
    difficulty = data.get("difficulty")
    user_id = request.sid
    room = USER_ROOM[user_id]

    if game_mode is None or difficulty is None:
        emit("error", {"message": "Missing data"})
        return

    difficulty = int(difficulty) // 1000

    try:
        global game

        if game_mode == "player":
            if room and len(ROOM_USERS[room]) == 2:
                if room in ROOM_USERS and len(ROOM_USERS[room]) == 2:
                    # Initialize the game instance for this room
                    ROOM_GAME[room] = BriscolaWeb(computer_count=0)
                    # Notify users in the room that the game has started
                    emit(
                        "game_state",
                        {"room": room, "game_state": ROOM_GAME[room].to_dict()},
                        room=room,
                    )
                else:
                    emit(
                        "error",
                        {"message": "Not enough players to start the game."},
                    )
            else:
                game = BriscolaWeb()
                emit("game_state", {"room": False, "game_state": game.to_dict()})

        elif game_mode == "computer":
            # Set up a game against the computer with a specified difficulty
            game = BriscolaWeb(
                computer_count=1,
                computer_logic_override=(basic_choice,),
                computer_skill_level=difficulty,
            )
            emit("game_state", {"room": False, "game_state": game.to_dict()})
        else:
            emit("error", {"message": "Invalid gameMode"})

    except Exception as e:
        emit("error", {"message": str(e)})


@app.route("/api/get_state", methods=["GET"])
def get_state() -> jsonify:
    return jsonify(game.to_dict() | {"player": "true"})


@app.route("/api/play_active_card", methods=["POST"])
def play_active_card() -> jsonify:
    if (res := request.json) is None:
        return jsonify({"error": "Invalid request"}), 400

    if (card_idx := res.get("card_index")) is None:
        return jsonify({"error": "Missing card index"}), 400
    game.active_player_play_card_idx(card_idx=card_idx)

    return jsonify(game.to_dict())


@app.route("/api/get_computer_choice", methods=["GET"])
def get_computer_choice() -> jsonify:
    return jsonify({"card_idx": game.play_card_computer(cards=game.active_player.hand.cards)})


@app.route("/api/end_play", methods=["GET"])
def end_play() -> jsonify:
    game.end_play()
    return jsonify(game.to_dict())


@app.route("/end_game")
def end_game() -> str:
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

    return render_template("end_game.html", winner_message=winner_message)


@socketio.on("connect")
def handle_connect():
    user_id = request.sid
    # Assign user to a default room or manage connection as needed
    USER_ROOM[user_id] = None
    emit("update_user_count", {"count": len(USER_ROOM.keys())}, broadcast=True)
    print(f"User connected: {user_id}, Total users: {len(USER_ROOM.keys())}")


@socketio.on("disconnect")
def handle_disconnect():
    user_id = request.sid
    room = USER_ROOM.pop(user_id, None)

    if room and room in ROOM_USERS:
        ROOM_USERS[room].remove(user_id)
        if not ROOM_USERS[room]:
            del ROOM_USERS[room]
        leave_room(room)
        emit("room_update", {"room": room, "users": list(ROOM_USERS[room])}, room=room)


@socketio.on("player_action")
def handle_player_action(data):
    card_index = data.get("card_index")
    if card_index is not None:
        game.active_player_play_card_idx(card_index)
        emit("game_state", game.to_dict(), broadcast=True)


@app.route("/api/get_room_users", methods=["GET"])
def get_room_users():
    room = request.args.get("room")
    if room in ROOM_USERS:
        return jsonify({"users": list(ROOM_USERS[room])})
    return jsonify({"error": "Room not found"}), 404


@socketio.on("join_game")
def handle_join_game(data):
    room = data.get("room")
    user_id = request.sid

    if room not in ROOM_USERS:
        ROOM_USERS[room] = set()

    join_room(room)
    ROOM_USERS[room] = ROOM_USERS[room] | {user_id}
    USER_ROOM[user_id] = room

    emit("room_update", {"room": room, "users": list(ROOM_USERS[room])}, room=room)


@socketio.on("leave_game")
def handle_leave_game(data):
    room = data.get("room")
    user_id = request.sid

    leave_room(room)

    if room:
        ROOM_USERS[room].remove(user_id)
        if user_id in USER_ROOM:
            del USER_ROOM[user_id]

    emit("room_update", {"room": room, "users": list(ROOM_USERS[room])})


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)

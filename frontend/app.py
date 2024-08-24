from flask import Flask, Response, jsonify, render_template, request

from backend.computer_logic.basic import basic_choice
from play_web.web_client import BriscolaWeb

app = Flask(__name__)
game = BriscolaWeb(computer_count=1, computer_logic_override=(basic_choice,))


@app.route("/")
def index() -> str:
    return render_template("index.html")


@app.route("/turn")
def turn() -> str:
    print(game.to_dict())
    return render_template("turn.html")


@app.route("/api/reset_state", methods=["POST"])
def reset_state() -> Response:
    if (res := request.json) is None:
        return jsonify({"error": "Invalid request"})

    if (game_mode := res.get("gameMode")) is None or (difficulty := res.get("difficulty")) is None:
        return jsonify({"error": "Missing gameMode"})

    difficulty = int(difficulty) // 1000

    try:
        global game
        print(f"Resetting game state to {game_mode} mode.")
        if game_mode == "local":
            game = BriscolaWeb()
        elif game_mode == "computer":
            game = BriscolaWeb(
                computer_count=1,
                computer_logic_override=(basic_choice,),
                computer_skill_level=difficulty,
            )
            print(game.computer_skill_level)
        else:
            return jsonify({"error": "Invalid gameMode"})

        print(f"Game state after reset: {game.to_dict()}")
        return jsonify(game.to_dict())
    except Exception as e:
        print(f"Error resetting game state: {str(e)}")
        return jsonify({"error": str(e)})


@app.route("/api/get_state", methods=["GET"])
def get_state() -> Response:
    return jsonify(game.to_dict() | {"local": "true"})


# TODO multiplayer?


@app.route("/api/play_active_card", methods=["POST"])
def play_active_card() -> Response:
    if (res := request.json) is None:
        return Response(status=400)

    if (card_idx := res.get("card_index")) is None:
        return Response(status=400)  # Bad request if card_index is not provided
    game.active_player_play_card_idx(card_idx=card_idx)

    return jsonify(game.to_dict())  # Return updated game state


@app.route("/api/get_computer_choice", methods=["GET"])
def get_computer_choice() -> Response:
    return jsonify({"card_idx": game.play_card_computer(cards=game.active_player.hand.cards)})


@app.route("/api/end_play", methods=["GET"])
def end_play() -> Response:
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


if __name__ == "__main__":
    app.run(debug=True)

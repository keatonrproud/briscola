from flask import Flask, Response, jsonify, render_template, request

from backend.setup import create_game_and_deal
from backend.turn import computer_choice_logic
from briscola.client import BriscolaGame
from card_game.table.table_settings import Direction
from play_web.web_logic import web_end_computer_play, web_play_card, web_play_computer_card

app = Flask(__name__)
game: BriscolaGame = create_game_and_deal(
    player_count=2, play_direction=Direction.COUNTER_CLOCKWISE, computer_count=1
)


@app.route("/")
def index() -> str:
    # reset the game and deck
    game.reset_game()
    return render_template("index.html")


@app.route("/turn")
def turn() -> str:
    return render_template("turn.html")


@app.route("/api/get_state", methods=["GET"])
def get_state() -> Response:
    return jsonify(game.to_dict())


# TODO how to visualize computer's plays?
#  when I play it goes to their turn and shows what I play, then their selection creates a played animation + show in active pile, then reset game state

# TODO option at start for local or vs computer

# TODO multiplayer?


@app.route("/api/play_human_card", methods=["POST"])
def play_human_card() -> Response:
    if (res := request.json) is None:
        return Response(status=400)

    if (card_idx := res.get("card_index")) is None:
        return Response(status=400)  # Bad request if card_index is not provided
    web_play_card(card_idx=card_idx, game=game)

    return jsonify(game.to_dict())  # Return updated game state


@app.route("/api/play_computer_card", methods=["POST"])
def play_computer_card() -> Response:
    if (res := request.json) is None:
        return Response(status=400)

    if (card_idx := res.get("card_index")) is None:
        return Response(status=400)  # Bad request if card_index is not provided

    web_play_computer_card(card_idx=card_idx, game=game)

    return jsonify(game.to_dict())


@app.route("/api/get_computer_choice", methods=["GET"])
def get_computer_choice() -> Response:
    print("choosing...")
    return jsonify(
        {"card_idx": computer_choice_logic(game=game, cards=game.active_player.hand.cards)}
    )


@app.route("/api/end_computer_turn", methods=["GET"])
def end_computer_turn() -> Response:
    print(game.turn_order())
    print(game.active_player)
    web_end_computer_play(game=game)

    print(game.active_player)

    print("========")

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

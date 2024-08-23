from flask import Flask, Response, jsonify, render_template, request

from backend.computer_logic.basic import basic_choice
from play_web.web_client import BriscolaWeb

app = Flask(__name__)
game = BriscolaWeb(computer_count=1, computer_logic_override=(basic_choice,))


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


# TODO prevent play before computer has gone
#  active_player should be the person whose turn/choice it is
#  shown_player should be the person whose cards are shown on a given turn (ie multiplayer, always show same shown_player)
#  if active_player != shown_player, input is not allowed

# TODO change turn info at bottom when computer goes, even though not active player

# TODO also separate player action into play --> show new active pile --> end turn

# TODO option at start for local or vs computer

# TODO active pile cards should move towards winning player then fade

# TODO add logging

# TODO multiplayer?


@app.route("/api/play_human_card", methods=["POST"])
def play_human_card() -> Response:
    if (res := request.json) is None:
        return Response(status=400)

    if (card_idx := res.get("card_index")) is None:
        return Response(status=400)  # Bad request if card_index is not provided
    game.player_play_card_idx(card_idx=card_idx)

    return jsonify(game.to_dict())  # Return updated game state


@app.route("/api/play_computer_card", methods=["POST"])
def play_computer_card() -> Response:
    if (res := request.json) is None:
        return Response(status=400)

    if (card_idx := res.get("card_index")) is None:
        return Response(status=400)  # Bad request if card_index is not provided

    game.active_player_play_card_idx(card_idx=card_idx)

    return jsonify(game.to_dict())


@app.route("/api/get_computer_choice", methods=["GET"])
def get_computer_choice() -> Response:
    return jsonify({"card_idx": game.play_card_computer(cards=game.active_player.hand.cards)})


@app.route("/api/end_computer_turn", methods=["GET"])
def end_computer_play() -> Response:
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

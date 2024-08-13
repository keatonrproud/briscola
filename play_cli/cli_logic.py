from subprocess import call
from time import sleep

from backend.turn import play_turn
from briscola_cards.briscola_card import BriscolaCard
from briscola_cards.briscola_player import BriscolaPlayer
from briscola_client import BriscolaGame
from play_cli.main import briscola_game


def cli_get_player_count():
    # response = input(f"Player count (2): \n")
    # if response not in "2":
    #     input("The player count must be 2. Input your player count: \n")
    # else:
    #     return int(response)
    return 2


def cli_print_briscola(game: BriscolaGame):
    print(f"Briscola Card: {game.briscola_card}\n")


def cli_print_played_cards(game: BriscolaGame):
    print(f"PILE: {game.active_pile}\n")


def cli_print_game_state(game: BriscolaGame):
    print(f"{len(game.deck.cards)}🃏 remain")
    print(
        "       ".join(
            [
                f"Player {player.player_num}: {player.score}pts"
                for player in game.players
            ]
        ),
        "\n",
    )


def cli_choose_card(game: BriscolaGame, player: BriscolaPlayer) -> BriscolaCard:
    cli_print_game_state(briscola_game)
    cli_print_briscola(game)
    sleep(0.25)

    if game.active_pile.cards:
        cli_print_played_cards(game)

    print(f"In Player {player.player_num}'s hand, there is: {player.hand}")

    while True:
        choice = input("Choose a card by inputting the number you want to play: ")

        try:
            choice = int(choice)
            assert 1 <= choice <= len(player.hand.cards)
        except ValueError:
            print("You must respond with a whole number!")
        except AssertionError:
            print("The number chosen must align with a card in the Player's hand.")
        else:
            break

    call("clear")

    return player.hand.cards[choice - 1]


def cli_play_game(game: BriscolaGame):
    while (
        # if player reaches game's win condition or no player has cards left, the game ends
        (max_score := max(player.score for player in game.players))
        <= game.win_condition
        and max(len(player.hand.cards) for player in game.players) > 0
    ):
        winning_card, winner, pts = play_turn(
            game=game, choose_card_method=cli_choose_card
        )
        print(f"========= Winning Card: {winning_card} =============")
        if pts != 0:
            print(
                f"======= Player {winner.player_num} went from {winner.score-pts} --> {winner.score}pts ======="
            )
        else:
            print(
                f"========= Player {winner.player_num} stays at {winner.score} ========="
            )
        print("=========================================\n")

    else:
        try:
            winner = next(
                player for player in game.players if player.score > game.win_condition
            )
            print(f"{winner} wins with {winner.score} points!")
        except StopIteration:
            tied_players = [
                f"Player {player.player_num}"
                for player in game.players
                if player.score == max_score
            ]
            print(
                f"The game ends with {' and '.join(tied_players)} having {max_score} points!"
            )

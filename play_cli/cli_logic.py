from logging import getLogger
from subprocess import call
from time import sleep

from backend.setup import create_game_and_deal, create_table_settings
from backend.turn import BriscolaTurnWinner, play_card_computer, play_turn
from briscola.card import BriscolaCard
from briscola.client import BriscolaGame
from briscola.player import BriscolaPlayer
from settings.game_settings import PLAY_DIRECTION

logger = getLogger(__name__)


def cli_get_player_count() -> int:
    # response = input(f"Player count (2): \n")
    # if response not in "2":
    #     input("The player count must be 2. Input your player count: \n")
    # else:
    #     return int(response)
    return 2


def cli_print_briscola(game: BriscolaGame) -> None:
    logger.info(f"Briscola Card: {game.briscola_card}\n")


def cli_print_played_cards(game: BriscolaGame) -> None:
    logger.info(f"PILE: {game.active_pile}\n")


def cli_print_game_state(game: BriscolaGame) -> None:
    logger.info(f"{len(game.deck.cards)}🃏 remain")
    logger.info(
        "       ".join([f"{player}: {player.score}pts" for player in game.players]),
        "\n",
    )


def cli_choose_card(game: BriscolaGame, player: BriscolaPlayer) -> BriscolaCard:
    cli_print_game_state(game)
    cli_print_briscola(game)
    sleep(0.25)

    if game.active_pile.cards:
        cli_print_played_cards(game)

    logger.info(f"{player}\n{player.hand}")

    if player.is_person:
        while True:
            try:
                choice = int(input("Choose a card by inputting the number you want to play: ")) - 1
                assert choice in range(len(player.hand.cards))
            except ValueError:
                logger.info("You must respond with a whole number!")
            except AssertionError:
                logger.info("The number chosen must align with a card in the Player's hand.")
            else:
                break
    else:
        choice = play_card_computer(game=game, cards=player.hand.cards)

    call("clear")
    return player.hand.cards[choice]


def cli_setup_game() -> BriscolaGame:
    table_settings = create_table_settings(cli_get_player_count(), PLAY_DIRECTION)
    game = create_game_and_deal(table_settings.player_count, PLAY_DIRECTION)

    return game


def cli_announce_scores(turn_winner: BriscolaTurnWinner) -> None:
    winning_card, winner, pts = (
        turn_winner.winning_card,
        turn_winner.winning_player,
        turn_winner.earned_pts,
    )
    logger.info(f"========= Winning Card: {winning_card} =============")
    if pts != 0:
        logger.info(
            f"======= Player {winner.player_num} went from {winner.score - pts} --> {winner.score}pts ======="
        )
    else:
        logger.info(f"========= Player {winner.player_num} stays at {winner.score} =========")
    logger.info("=========================================\n")


def cli_announce_winner(game: BriscolaGame) -> None:
    max_score = max(player.score for player in game.players)
    try:
        winner = next(player for player in game.players if player.score > game.win_condition)
        logger.info(f"{winner} wins with {winner.score} points!")
    except StopIteration:
        tied_players = [f"{player}" for player in game.players if player.score == max_score]
        logger.info(f"The game ends with {' and '.join(tied_players)} having {max_score} points!")


def cli_play_game(game: BriscolaGame) -> None:
    while game.game_ongoing:
        turn_winner = play_turn(game=game, choose_card_method=cli_choose_card)
        cli_announce_scores(turn_winner)
    else:
        cli_announce_winner(game=game)

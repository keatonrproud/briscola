import logging
from pprint import pprint
from typing import Callable

from backend.computer_logic.basic import basic_choice
from backend.computer_logic.random_ import random_choice
from backend.setup import create_game_and_deal
from play_cli.cli_logic import cli_play_game

logger = logging.getLogger(__name__)
# TODO make the logic/choice a ComputerLogic object

# TODO add computer logic to CLI

N_TEST_GAMES = 1_000


def play_game(logics: tuple[Callable, ...], first_dealer: int | None = -1) -> dict[str, int]:
    """Play a game, and return the scores for each logic."""
    game = create_game_and_deal(
        player_count=2,
        computer_count=2,
        logic_override=logics,
        first_dealer=first_dealer,
    )

    cli_play_game(game)

    return {player.computer_logic_override.__name__: player.score for player in game.players}


def main(logics: tuple[Callable,], log_cli: bool = False) -> None:
    """Run the Monte Carlo to test the computer's logic."""
    logger_level = logging.DEBUG if log_cli else logging.CRITICAL
    logging.basicConfig(level=logger_level)

    dealer_options: tuple[str | int, ...] = ("random", *range(len(logics)))

    names = [logic.__name__ for logic in logics]

    print(f"Testing {' vs '.join(names)} over {N_TEST_GAMES:,} per dealer variation...\n")

    full_sum_scores = {name: 0 for name in names}
    for dealer_option in dealer_options:
        total_scores = {name: 0 for name in names}
        for game_num in range(N_TEST_GAMES):
            if N_TEST_GAMES % (game_num + 1) / 10 == 0:
                logger.warning(game_num + 1)
            dealer_idx = dealer_option if dealer_option != "random" else game_num % 2
            game_scores = play_game(logics=logics, first_dealer=dealer_idx)

            for name in names:
                total_scores[name] += game_scores[name]

        for name in names:
            full_sum_scores[name] += total_scores[name]

        print(f"Dealer: {names[dealer_option] if dealer_option != 'random' else dealer_option}")
        pprint(total_scores)
        print("==========\n")

    print("Complete scores:")
    pprint(full_sum_scores)
    print("==========\n")

    winner = max(full_sum_scores, key=lambda x: full_sum_scores[x])
    loser = min(full_sum_scores, key=lambda x: full_sum_scores[x])
    print(
        f"The best performer was {winner}, winning by {full_sum_scores[winner]/full_sum_scores[loser]-1:.1%}"
    )
    print("==========\n")


if __name__ == "__main__":
    main(logics=(basic_choice, random_choice), log_cli=False)
    main(logics=(random_choice, basic_choice), log_cli=False)

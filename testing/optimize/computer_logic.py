from pprint import pprint
from typing import Callable

from src.backend import basic_choice
from src.backend import random_choice
from config import build_logger
from play.cli.cli_client import BriscolaCLI

logger = build_logger(__name__)

N_TEST_GAMES = 1_000


def play_game(
    logics: tuple[Callable, ...], first_dealer: int | None = -1, computer_skill_level: int = 10
) -> dict[str, int]:
    """Play a game, and return the scores for each logic."""
    game = BriscolaCLI(
        computer_count=2,
        computer_logic_override=logics,
        computer_skill_level=computer_skill_level,
        first_dealer=first_dealer,
    )
    game.play_game()

    return {
        player.computer_logic_override.__name__: player.score
        for player in game.players
        if player.computer_logic_override is not None
    }


def main(logics: tuple[Callable, ...], computer_skill_level: int = 10) -> None:
    """Run the Monte Carlo to test the computer's logic."""
    dealer_options: tuple[None | int, ...] = (None,)  # (None, *range(len(logics)))

    names = [logic.__name__ for idx, logic in enumerate(logics)]

    print(f"Testing {' vs '.join(names)} over {N_TEST_GAMES:,} per dealer variation...\n")

    full_sum_scores = {name: 0 for name in names}
    wins = {name: 0 for name in names}
    for dealer_option in dealer_options:
        total_scores = {name: 0 for name in names}
        for game_num in range(N_TEST_GAMES):
            if game_num == N_TEST_GAMES // 2:
                logger.debug(f"Game #{game_num+1}")
            dealer_idx = dealer_option if dealer_option is not None else game_num % 2

            game_scores = play_game(
                logics=logics, first_dealer=dealer_idx, computer_skill_level=computer_skill_level
            )

            for name in names:
                total_scores[name] += game_scores[name]

            winner = max(game_scores, key=lambda x: game_scores[x])
            wins[winner] += 1

        for name in names:
            full_sum_scores[name] += total_scores[name]

        print(f"Dealer: {'random' if dealer_option is None else names[dealer_option]}")
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
    print("\n\n\n")

    print("wins", wins)


if __name__ == "__main__":
    skill = 0  # 10 means fully based on the choice, 0 means completely random

    main(logics=(basic_choice, random_choice), computer_skill_level=skill)

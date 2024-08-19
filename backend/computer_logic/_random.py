from random import choice

from briscola.card import BriscolaCard
from briscola.client import BriscolaGame


def random_choice(cards: list[BriscolaCard], **kwargs: BriscolaGame) -> int:
    return choice(range(len(cards)))

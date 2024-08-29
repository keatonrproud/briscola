from random import choice

from card_games.briscola.card import BriscolaCard


def random_choice(cards: list[BriscolaCard]) -> int:
    return choice(range(len(cards)))

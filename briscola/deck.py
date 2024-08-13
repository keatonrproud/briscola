from typing import Generator

from briscola.card import BriscolaCard
from briscola.card_settings import CARD_INFOS, SUITS, BriscolaCardNumber
from card_game.cards.deck import Deck


def generate_cards() -> Generator[BriscolaCard, None, None]:
    for suit in SUITS:
        for number in BriscolaCardNumber:
            yield BriscolaCard(number=number, suit=suit, card_info=CARD_INFOS[number])


class BriscolaDeck(Deck):

    def __init__(self) -> None:
        super().__init__(deck_type="BRISCOLA", card_set=list(generate_cards()))

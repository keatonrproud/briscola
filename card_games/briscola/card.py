from typing import Any

from card_games.briscola.card_settings import BriscolaCardInfo, BriscolaCardNumber
from card_games.general.cards.card import Card
from card_games.general.cards.suits import Suit


class BriscolaCard(Card):
    def __init__(self, number: BriscolaCardNumber, suit: Suit, card_info: BriscolaCardInfo) -> None:
        super().__init__(number=number, suit=suit)
        self.strength = card_info.strength
        self.points = card_info.points

    def __eq__(self, other: Any) -> bool:
        return self.number == other.number and self.suit == other.suit

    def __lt__(self, other: Any) -> bool:
        return self.strength < other.strength

    def to_dict(self) -> dict:
        return {
            "number": self.number.to_dict(),
            "suit": self.suit.to_dict(),
            "strength": self.strength,
            "points": self.points,
        }

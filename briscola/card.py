from briscola.card_settings import BriscolaCardInfo, BriscolaCardNumber
from card_game.cards.card import Card
from card_game.cards.suits import Suit


class BriscolaCard(Card):
    def __init__(self, number: BriscolaCardNumber, suit: Suit, card_info: BriscolaCardInfo):
        super().__init__(number=number, suit=suit)
        self.strength = card_info.strength
        self.points = card_info.points

    def __eq__(self, other):
        return self.number == other.number and self.suit == other.suit

    def __lt__(self, other):
        return self.strength < other.strength

from card_games.briscola.card import BriscolaCard
from card_games.general.cards.hand import Hand


class BriscolaHand(Hand):
    def __init__(self, cards: list[BriscolaCard]):
        super().__init__(cards=cards, max_cards=3, min_cards=0)
        self.cards = cards

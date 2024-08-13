from card_game.cards.suits import Suit
from card_game.cards.numbers import CardNumber

class Card:
    def __init__(self, number: CardNumber, suit: Suit):
        self.number = number
        self.suit = suit

    def __repr__(self):
        return f"{self.number.name}{self.suit}"

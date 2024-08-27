from card_games.general.cards.numbers import CardNumber
from card_games.general.cards.suits import Suit


class Card:
    def __init__(self, number: CardNumber, suit: Suit):
        self.number = number
        self.suit = suit

    def __repr__(self) -> str:
        return f"{self.number.name}{self.suit}"

    def to_dict(self) -> dict:
        return {"number": self.number.to_dict(), "suit": self.suit.to_dict()}

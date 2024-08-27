from typing import Generic

from card_games.general.generics.card import CARD


class Hand(Generic[CARD]):
    def __init__(
        self,
        cards: list[CARD],
        max_cards: int | None = None,
        min_cards: int | None = None,
    ):
        self.cards = cards
        self.max_cards = max_cards
        self.min_cards = min_cards

    def draw_cards(self, cards_drawn: list[CARD]) -> None:
        self.cards += cards_drawn

    def __repr__(self) -> str:
        return f'{", ".join(f"{{{idx+1}}}-{card}" for idx, card in enumerate(self.cards))}'

    def to_dict(self) -> dict:
        return {
            "cards": [card.to_dict() for card in self.cards],
            "max_cards": self.max_cards,
            "min_cards": self.min_cards,
        }

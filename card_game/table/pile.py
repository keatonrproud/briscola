from typing import Generic

from generics.card import CARD


class Pile(Generic[CARD]):
    def __init__(self, cards: list[CARD], face_up: bool = True):
        self.cards = cards
        self.face_up = face_up

    def add_cards(self, cards: list[CARD]) -> None:
        """Add these cards to the pile, in order from first to last."""
        self.cards += cards

    def remove_card(self, card: CARD) -> None:
        self.cards.remove(card)

    def keep_only_recent_cards(self, num_to_keep: int = 1) -> list[CARD]:
        leftover_cards = self.cards[:-num_to_keep]
        self.cards = self.cards[-num_to_keep:]
        return leftover_cards

    def clear_pile(self) -> None:
        self.cards = []

from random import shuffle
from typing import Generic

from card_games.general.table.pile import Pile
from generics.card import CARD
from generics.player import PLAYER


class UnlimitedHandSizeException(Exception):
    """Exception raised when a hand size is considered unlimited or exceeds allowed limits."""


class Deck(Pile, Generic[CARD, PLAYER]):
    def __init__(self, deck_type: str, card_set: list[CARD]):
        super().__init__(cards=card_set, face_up=False)
        self.deck_type = deck_type
        self.card_set = card_set
        self.current_cards = card_set

        self.reset_deck()

    def __repr__(self) -> str:
        return f"Deck Info: {self.deck_type} w/ {len(self.cards)} cards left"

    def to_dict(self) -> dict:
        return {
            "current_cards": [card.to_dict() for card in self.current_cards],
            "card_set": [card.to_dict() for card in self.card_set],
        }

    def shuffle(self) -> None:
        shuffle(self.current_cards)

    def deal(self, players: list[PLAYER], cards_in_hand: int) -> list[list[CARD]]:
        for player in players:
            player.hand.cards = self.draw_cards(draw_count=cards_in_hand)

        return [player.hand.cards for player in players]

    def fill_hands(self, players: list[PLAYER], max_cards_in_hand: int | None) -> None:
        if max_cards_in_hand is None:
            raise UnlimitedHandSizeException("Max hand size must be declared to fill the hands.")

        for player in players:
            num_cards_missing = max_cards_in_hand - len(player.hand.cards)
            player.hand.cards += self.draw_cards(num_cards_missing)

    def reset_deck(self) -> None:
        self.current_cards = self.card_set
        self.shuffle()

    def draw(self) -> CARD:
        return self.draw_cards(draw_count=1)[0]

    def draw_cards(self, draw_count: int = 1) -> list[CARD]:
        return [self.current_cards.pop() for _ in range(min(draw_count, len(self.current_cards)))]

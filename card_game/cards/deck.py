from card_game.cards.card import Card
from card_game.table.pile import Pile
from random import shuffle
from card_game.table.player import Player


class Deck(Pile):
    def __init__(self, deck_type: str, card_set: list[Card]):
        super().__init__(cards=card_set, face_up=False)
        self.deck_type = deck_type
        self.card_set = card_set
        self.current_cards = card_set

        self.reset_deck()

    def __repr__(self):
        return f"Deck Info: {self.deck_type} w/ {len(self.cards)} cards left"

    def shuffle(self) -> None:
        shuffle(self.current_cards)

    def deal(self, players: list[Player], cards_in_hand: int) -> list[list[Card]]:
        for player in players:
            hand = self.draw_cards(draw_count=cards_in_hand)
            player.hand.cards = hand

        return [player.hand for player in players]

    def fill_hands(self, players: list[Player], max_cards_in_hand: int) -> None:
        for player in players:
            num_cards_missing = max_cards_in_hand - len(player.hand.cards)
            player.hand.cards += self.draw_cards(num_cards_missing)

    def reset_deck(self):
        self.current_cards = self.card_set
        self.shuffle()

    def draw(self) -> Card:
        return self.draw_cards(draw_count=1)[0]

    def draw_cards(self, draw_count: int = 1) -> list[Card]:
        return [self.current_cards.pop() for _ in range(draw_count)]

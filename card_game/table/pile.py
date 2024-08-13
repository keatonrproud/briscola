from card_game.cards.card import Card


class Pile:
    def __init__(self, cards: list[Card], face_up: bool = True):
        self.cards = cards
        self.face_up = face_up

    def add_cards(self, cards: list[Card]) -> None:
        """Add these cards to the pile, in order from first to last."""
        self.cards += cards

    def remove_card(self, card: Card) -> None:
        self.cards.remove(card)

    def keep_only_recent_cards(self, num_to_keep: int = 1) -> list[Card]:
        leftover_cards = self.cards[:-num_to_keep]
        self.cards = self.cards[-num_to_keep:]
        return leftover_cards

    def clear_pile(self) -> None:
        self.cards = []

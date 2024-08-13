from card_game.cards.card import Card


class Hand:

    def __init__(self, cards: list[Card], max_cards: int | None = None, min_cards: int | None = None):
        self.cards = cards
        self.max_cards = max_cards
        self.min_cards = min_cards

    def draw_cards(self, cards_drawn: list[Card]):
        self.cards += cards_drawn

    def __repr__(self):
        return f'[{", ".join(f"{{{idx+1}}}-{card}" for idx, card in enumerate(self.cards))}]'

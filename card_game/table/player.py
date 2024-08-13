from card_game.cards.card import Card
from card_game.cards.hand import Hand


class Player:
    def __init__(
        self,
        player_num: int,
        hand: Hand = None,
        captured_cards: list[Card] = None,
        score: int = 0,
        in_game: bool = True,
    ):
        self.player_num = player_num
        self.hand = hand if hand is not None else Hand(cards=[])
        self.captured_cards = captured_cards if captured_cards is not None else []
        self.score = score
        self.in_game = in_game

    def __repr__(self):
        return (
            f"Player {self.player_num} ({self.score} pts)\n"
            f"  -- Hand:  {self.hand}\n"
        )

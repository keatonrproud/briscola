from enum import Enum
from random import choice

from card_games.general.cards.card import Card
from card_games.general.cards.hand import Hand


class PlayerColor(Enum):
    BLUE = "🟦"
    GREEN = "🟩"
    RED = "🟥"
    YELLOW = "🟨"


class Player:
    def __init__(
        self,
        player_num: int,
        hand: Hand = Hand(cards=[]),
        captured_cards: list[Card] | None = None,
        score: int = 0,
        in_game: bool = True,
        color: PlayerColor = choice(list(PlayerColor)),
        is_person: bool = True,
        unique_player_type=False,
    ):
        self.player_num = player_num
        self.hand = hand if hand is not None else Hand(cards=[])
        self.captured_cards = captured_cards if captured_cards is not None else []
        self.score = score
        self.in_game = in_game
        self.color = color
        self.is_person = is_person
        self.unique_player_type = unique_player_type

    def __repr__(self) -> str:
        player_type = "Player" if self.is_person else "Computer"
        repr = f"{self.color.value} {player_type}"
        if not self.unique_player_type:
            repr += f" {self.player_num}"
        return repr

    def to_dict(self) -> dict:
        return {
            "player_num": self.player_num,
            "hand": self.hand.to_dict(),
            "captured_cards": [card.to_dict() for card in self.captured_cards],
            "score": self.score,
            "in_game": self.in_game,
            "color": self.color.value,
            "is_person": self.is_person,
            "repr": self.__repr__(),
        }

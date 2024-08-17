from enum import Enum
from random import choice

from briscola.card import BriscolaCard
from briscola.hand import BriscolaHand
from card_game.table.player import Player


class PlayerColor(Enum):
    BLUE = "🟦"
    GREEN = "🟩"
    RED = "🟥"
    YELLOW = "🟨"


class BriscolaPlayer(Player):
    cards: list[BriscolaCard]
    hand: BriscolaHand

    def __init__(self, player_num: int, color: PlayerColor = choice(list(PlayerColor))):
        super().__init__(
            player_num=player_num,
            hand=BriscolaHand(cards=[]),
            captured_cards=None,
            score=0,
            in_game=True,
        )
        self.color = color

    def __repr__(self) -> str:
        return super().__repr__() + f" {self.color.value}"

from random import choice
from typing import Callable, Optional

from briscola.hand import BriscolaHand
from card_game.table.player import Player, PlayerColor


class BriscolaPlayer(Player):
    hand: BriscolaHand
    computer_logic_override: Optional[Callable] = None

    def __init__(self, player_num: int, color: PlayerColor = choice(list(PlayerColor))):
        super().__init__(
            player_num=player_num,
            hand=BriscolaHand(cards=[]),
            captured_cards=None,
            score=0,
            in_game=True,
            color=color,
        )

from random import choice
from typing import Callable, Optional

from briscola.hand import BriscolaHand
from card_game.table.player import Player, PlayerColor


class BriscolaPlayer(Player):
    hand: BriscolaHand
    computer_logic_override: Optional[Callable] = None
    skill_level: int | None = 10

    def __init__(self, player_num: int, color: PlayerColor = choice(list(PlayerColor))):
        super().__init__(
            player_num=player_num,
            hand=BriscolaHand(cards=[]),
            captured_cards=None,
            score=0,
            in_game=True,
            color=color,
        )

    def __repr__(self) -> str:
        logic_method = (
            self.computer_logic_override.__name__
            if self.computer_logic_override is not None
            else ""
        )
        repr = super().__repr__()
        if logic_method:
            repr += f" {logic_method}"
        return repr

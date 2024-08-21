from typing import Callable

from briscola.client import BriscolaGame
from logging_config import build_logger

logger = build_logger(__name__)


class BriscolaWeb(BriscolaGame):

    def __init__(
        self,
        computer_count: int = 0,
        computer_logic_override: tuple[Callable, ...] = (),
        computer_skill_level: int = 10,
        first_dealer: int | None = -1,
    ):
        super().__init__(
            computer_count=computer_count,
            computer_logic_override=computer_logic_override,
            computer_skill_level=computer_skill_level,
            first_dealer=first_dealer,
        )

    @staticmethod
    def get_player_count() -> int:
        # response = input(f"Player count (2): \n")
        # if response not in "2":
        #     input("The player count must be 2. Input your player count: \n")
        # else:
        #     return int(response)
        return 2

    def active_player_play_card_idx(self, card_idx: int) -> None:
        card_to_play = self.active_player.hand.cards[card_idx]
        self.play_card(self.active_player, card_to_play)

    def player_play_card_idx(self, card_idx: int) -> None:
        self.active_player_play_card_idx(card_idx)
        self.end_play()

    def end_play(self) -> None:
        if self.active_player == self.turn_order()[-1]:
            self.end_turn()
        else:
            current_player_idx = self.turn_order().index(self.active_player)
            next_player_idx = (
                current_player_idx + 1 if current_player_idx + 1 != len(self.turn_order()) else 0
            )
            self.active_player = self.turn_order()[next_player_idx]

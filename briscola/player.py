from briscola.card import BriscolaCard
from briscola.hand import BriscolaHand
from card_game.table.player import Player


class BriscolaPlayer(Player):
    cards: list[BriscolaCard]
    hand: BriscolaHand

    def __init__(self, player_num: int):
        super().__init__(
            player_num=player_num,
            hand=BriscolaHand(cards=[]),
            captured_cards=None,
            score=0,
            in_game=True,
        )

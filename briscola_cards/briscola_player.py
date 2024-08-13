from card_game.table.player import Player
from briscola_cards.briscola_hand import BriscolaHand


class BriscolaPlayer(Player):
    def __init__(self, player_num: int):
        super().__init__(
            player_num=player_num,
            hand=BriscolaHand(cards=[]),
            captured_cards=None,
            score=0,
            in_game=True,
        )

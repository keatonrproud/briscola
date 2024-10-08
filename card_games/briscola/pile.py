from card_games.briscola.card import BriscolaCard
from card_games.general.table.pile import Pile


class BriscolaPile(Pile[BriscolaCard]):

    def __init__(self, cards: list[BriscolaCard], face_up: bool = True):
        super().__init__(cards=cards, face_up=face_up)

    def __repr__(self) -> str:
        return ", ".join([f"{card}" for card in self.cards])

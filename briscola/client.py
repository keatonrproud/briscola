from typing import Final

from briscola.card import BriscolaCard
from briscola.deck import BRISCOLA_DECK
from briscola.pile import BriscolaPile
from briscola.player import BriscolaPlayer
from card_game.cards.card import Card
from card_game.cards.suits import Suit
from card_game.game_client import CardGame
from card_game.table.table_settings import TableSettings


class BriscolaGame(CardGame):
    briscola: Suit | None = None
    briscola_card: Card | None = None
    max_cards_in_hand: int = 3
    active_pile: BriscolaPile = BriscolaPile(cards=[], face_up=True)
    players: list[BriscolaPlayer]
    win_condition: Final = 60
    dealer: BriscolaPlayer

    def __init__(
        self,
        table_settings: TableSettings,
        players: list[BriscolaPlayer],
        first_dealer: BriscolaPlayer = None,
    ):
        super().__init__(
            table_settings=table_settings,
            deck=BRISCOLA_DECK,
            players=players,
            first_dealer=first_dealer,
        )

    def __repr__(self) -> str:
        return f"Briscola Card: {self.briscola_card}\n" f"----\n" f"{super().__repr__()}"

    def deal_hands(self, cards_in_hand: int, change_dealers: bool = True) -> list[list[Card]]:
        # if briscola_card hasn't been set yet, then draw and set the briscola card first
        if self.briscola_card is None:
            self.briscola_card = self.deck.draw()
            self.briscola = self.briscola_card.suit
            # briscola card should be treated as the last card of the deck
            self.deck.cards.insert(0, self.briscola_card)
        return super().deal_hands(cards_in_hand=cards_in_hand, change_dealers=change_dealers)

    def fill_hands(self, max_cards_in_hand: int = None) -> None:
        return self.deck.fill_hands(
            players=self.players,
            max_cards_in_hand=self.max_cards_in_hand or max_cards_in_hand,
        )

    def play_card(self, player: BriscolaPlayer, card: BriscolaCard):
        player.hand.cards.remove(card)
        self.active_pile.cards.append(card)

    def get_turn_order(self) -> list[BriscolaPlayer]:
        dealer_idx = self.players.index(self.dealer)
        first_player_idx = dealer_idx + 1 if dealer_idx < len(self.players) - 1 else 0
        return self.players[first_player_idx:] + self.players[:first_player_idx]

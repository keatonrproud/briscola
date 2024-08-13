from typing import Generic

from card_game.table.table_settings import TableSettings
from generics.card import CARD
from generics.deck import DECK
from generics.player import PLAYER


class CardGame(Generic[DECK, PLAYER, CARD]):
    def __init__(
        self,
        table_settings: TableSettings,
        deck: DECK,
        players: list[PLAYER],
        first_dealer: PLAYER | None = None,
    ):
        self.table_settings = table_settings
        self.deck = deck
        self.players = players
        self.first_dealer = first_dealer
        self.dealer = first_dealer if first_dealer is not None else self.players[-1]

    def __repr__(self) -> str:
        game_info = f"{self.table_settings}{self.deck}"
        player_info = "".join([str(player) for player in self.players])
        return game_info + "\n----\n" + player_info

    def get_turn_order(self) -> list[PLAYER]:
        dealer_idx = self.players.index(self.dealer)
        first_player_idx = dealer_idx + 1 if dealer_idx < len(self.players) - 1 else 0
        return self.players[first_player_idx:] + self.players[:first_player_idx]

    @property
    def scores(self) -> list[int]:
        return [player.score for player in self.players]

    def deal_hands(self, cards_in_hand: int, change_dealers: bool = True) -> list[list[CARD]]:
        if change_dealers:
            self.change_dealers()
        return self.deck.deal(players=self.players, cards_in_hand=cards_in_hand)

    def fill_hands(self, max_cards_in_hand: int) -> None:
        return self.deck.fill_hands(players=self.players, max_cards_in_hand=max_cards_in_hand)

    def draw_card(self, player: PLAYER, draw_count: int = 0) -> None:
        player.hand.cards += self.deck.draw_cards(draw_count=draw_count)

    def change_dealers(self) -> None:
        dealer_index = self.players.index(self.dealer)
        if dealer_index + 1 == len(self.players):
            self.dealer = self.players[0]
        else:
            self.dealer = self.players[dealer_index + 1]

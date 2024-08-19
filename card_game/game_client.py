from abc import ABC, abstractmethod
from typing import Generic

from card_game.table.table_settings import TableSettings
from generics.card import CARD
from generics.deck import DECK
from generics.player import PLAYER


class CardGame(Generic[DECK, PLAYER, CARD], ABC):
    last_winner: PLAYER | None = None

    def __init__(
        self,
        table_settings: TableSettings,
        deck: DECK,
    ):
        self.table_settings = table_settings
        self.deck = deck
        self.players = self.create_players(player_count=self.table_settings.player_count)
        self.dealer = self.players[-1]
        self.active_player = self.players[0]

    def __repr__(self) -> str:
        game_info = f"{self.table_settings}{self.deck}"
        player_info = "".join([str(player) for player in self.players])
        return game_info + "\n----\n" + player_info

    def turn_order(self) -> list[PLAYER]:
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

    @abstractmethod
    def create_players(self, player_count: int) -> list[PLAYER]:
        """A method to generate players for the game, given a player_count."""

    def change_dealers(self) -> None:
        dealer_index = self.players.index(self.dealer)
        if dealer_index + 1 == len(self.players):
            self.dealer = self.players[0]
        else:
            self.dealer = self.players[dealer_index + 1]

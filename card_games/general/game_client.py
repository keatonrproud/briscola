from abc import ABC, abstractmethod
from functools import cached_property
from typing import Generic

from card_games.general.table.table_settings import Direction, TableSettings
from config.logging_config import build_logger
from card_games.general.generics.card import CARD
from card_games.general.generics.deck import DECK
from card_games.general.generics.player import PLAYER
from random import choice
logger = build_logger(__name__)


class CardGame(Generic[DECK, PLAYER, CARD], ABC):
    last_winner: PLAYER | None = None

    def __init__(self, deck: DECK, first_dealer_idx: int | None = None, computer_count: int = 0):
        self.deck = deck
        self.computer_count = computer_count

        assert first_dealer_idx is None or first_dealer_idx < len(self.players), "The first_dealer_idx must be an index less than the number of players in the game."
        self.first_dealer_idx = first_dealer_idx if first_dealer_idx is not None else choice(range(len(self.players)))
        self.dealer = self.players[self.first_dealer_idx]
        first_player_idx = self.first_dealer_idx+1 if self.first_dealer_idx < len(self.players)-1 else 0
        self.active_player = self.players[first_player_idx]

        try:
            # show the active player if it's a person, otherwise the first person-player
            self.shown_player = (
                self.active_player
                if self.active_player.is_person
                else next(p for p in self.players if p.is_person)
            )
        except StopIteration:
            # if there are no person-players, then show the first computer in the list
            self.shown_player = self.players[0]

        logger.debug(
            f"First dealer is {self.dealer}, first player is {self.active_player}, shown player is {self.shown_player}."
        )

    def __repr__(self) -> str:
        game_info = f"{self.table_settings}{self.deck}"
        player_info = "".join([str(player) for player in self.players])
        return game_info + "\n----\n" + player_info

    def turn_order(self) -> list[PLAYER]:
        logger.debug(f"Dealer is {self.dealer}")
        dealer_idx = self.players.index(self.dealer)
        first_player_idx = dealer_idx + 1 if dealer_idx < len(self.players) - 1 else 0

        turn_order = self.players[first_player_idx:] + self.players[:first_player_idx]

        return turn_order

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
    @cached_property
    def players(self) -> list[PLAYER]:
        """A method to generate and access players for the game."""

    def change_dealers(self) -> None:
        dealer_index = self.players.index(self.dealer)
        if dealer_index + 1 == len(self.players):
            self.dealer = self.players[0]
        else:
            self.dealer = self.players[dealer_index + 1]
        logger.debug(f"New dealer is {self.dealer}")

    @staticmethod
    @abstractmethod
    def get_player_count() -> int:
        """A method to return the number of players for the game."""

    @abstractmethod
    @cached_property
    def play_direction(self) -> Direction:
        """A method to return the direction of play."""

    @cached_property
    def table_settings(self) -> TableSettings:
        return TableSettings(
            player_count=self.get_player_count(),
            turn_direction=self.play_direction,
            computer_count=self.computer_count,
        )

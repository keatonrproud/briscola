from abc import ABC
from dataclasses import dataclass
from functools import cached_property
from random import choice
from typing import Callable, Final

from card_games.briscola.card import BriscolaCard
from card_games.briscola.deck import BriscolaDeck
from card_games.briscola.game_settings import CARDS_IN_HAND, PLAY_DIRECTION
from card_games.briscola.pile import BriscolaPile
from card_games.briscola.player import BriscolaPlayer
from card_games.general.cards.card import Card
from card_games.general.cards.suits import Suit
from card_games.general.game_client import CardGame
from card_games.general.table.player import PlayerColor
from card_games.general.table.table_settings import Direction
from config.logging_config import build_logger
from other.computer_logic.random_ import random_choice

logger = build_logger(__name__)


@dataclass
class BriscolaTurnWinner:
    winning_card: BriscolaCard
    winning_player: BriscolaPlayer
    earned_pts: int
    losing_cards: list[BriscolaCard]


class BriscolaGame(CardGame, ABC):
    briscola: Suit | None = None
    briscola_card: BriscolaCard | None = None
    max_cards_in_hand: int = 3
    active_pile: BriscolaPile = BriscolaPile(cards=[], face_up=True)
    win_condition: Final = 60

    def __init__(
        self,
        computer_count: int = 0,
        computer_logic_override: tuple[Callable, ...] = (),
        computer_skill_level: int = 10,
        first_dealer: int | None = None,
        online: bool = False,
    ):
        self.online = online
        self.computer_logic_override = computer_logic_override
        self.computer_skill_level = computer_skill_level
        super().__init__(
            deck=BriscolaDeck(), first_dealer_idx=first_dealer, computer_count=computer_count
        )
        self.clear_pile()
        self.deal_hands(cards_in_hand=CARDS_IN_HAND, change_dealers=False)

    def __repr__(self) -> str:
        return f"Briscola: {self.briscola_card}\n" f"----\n" f"{super().__repr__()}"

    @cached_property
    def play_direction(self) -> Direction:
        """A method to return the direction of play."""
        return PLAY_DIRECTION

    def deal_hands(
        self, cards_in_hand: int = CARDS_IN_HAND, change_dealers: bool = True
    ) -> list[list[Card]]:
        # if briscola_card hasn't been set yet, then draw and set the briscola card first
        if self.briscola_card is None:
            self.briscola_card = self.deck.draw()
            self.briscola = self.briscola_card.suit
            # briscola card should be treated as the last card of the generics
            self.deck.cards.insert(0, self.briscola_card)
        return super().deal_hands(cards_in_hand=cards_in_hand, change_dealers=change_dealers)

    def fill_hands(self, max_cards_in_hand: int | None = None) -> None:
        return super().fill_hands(
            max_cards_in_hand=self.max_cards_in_hand or max_cards_in_hand,
        )

    def play_card(self, player: BriscolaPlayer, card: BriscolaCard) -> BriscolaCard:
        player.hand.cards.remove(card)
        self.active_pile.cards.append(card)
        return card

    def play_card_computer(
        self,
        cards: list[BriscolaCard],
    ) -> int:

        # (1 - skill_level) * 10 is the percent chance of computer choosing a card randomly
        if choice(range(9)) >= self.computer_skill_level:
            logger.debug("Making a random choice due to computer skill level.")
            return random_choice(cards)

        if len(self.players) > 2:
            raise NotImplementedError()

        assert type(self.briscola) is Suit

        logic = self.active_player.computer_logic_override

        return (
            random_choice(cards=cards)
            if logic is None or logic == random_choice
            else logic(briscola=self.briscola, active_pile=self.active_pile, cards=cards)
        )

    @property
    def game_ongoing(self) -> bool:
        return sum(player.score for player in self.players) < 120

    def reset_game(self) -> None:
        self.briscola, self.briscola_card = None, None
        self.deck = BriscolaDeck()

        super().__init__(
            deck=self.deck,
            first_dealer_idx=self.first_dealer_idx,
            computer_count=self.computer_count,
        )

        self.clear_pile()
        self.deal_hands(cards_in_hand=CARDS_IN_HAND, change_dealers=False)

    @cached_property
    def players(self) -> list[BriscolaPlayer]:
        colors = list(PlayerColor)
        players = [
            BriscolaPlayer(player_num=num + 1, color=colors[num])
            for num in range(self.table_settings.player_count)
        ]

        # set players as computers working from the end of the player list
        for computer_idx in range(0, self.computer_count):
            computer = players[-(computer_idx + 1)]
            computer.is_person = False

        # if there is only one human player, set it as a unique type to make its __repr__ avoid player_num
        if self.table_settings.player_count - self.computer_count == 1:
            players[0].unique_player_type = True

        if self.computer_count > 0:
            # if there is only one computer, set it as a unique type to make its __repr__ avoid player_num
            if self.computer_count == 1:
                computer = next(player for player in players if not player.is_person)
                computer.unique_player_type = True

            assert (
                len(self.computer_logic_override) > 0
            ), "You must include at least one computer logic override for your computers."
            self.set_computer_logic(computers=players[-self.computer_count :])

        return players

    @staticmethod
    def calculate_points(captured_cards: list[BriscolaCard]) -> int:
        return sum(card.points for card in captured_cards)

    def set_computer_logic(self, computers: list[BriscolaPlayer]) -> None:
        for idx, computer in enumerate(computers):
            computer.is_person = False
            computer.skill_level = self.computer_skill_level

            # set computer logic as the same idx a the override, or the first if there's no matching override
            try:
                computer.computer_logic_override = self.computer_logic_override[idx]
            except IndexError:
                computer.computer_logic_override = self.computer_logic_override[0]

    def clear_pile(self) -> None:
        self.active_pile.clear_pile()

    def get_winning_card(self) -> tuple[BriscolaCard, BriscolaPlayer]:
        played_cards = self.active_pile.cards
        trump_suit = (
            self.briscola
            if len([card for card in played_cards if card.suit == self.briscola])
            else played_cards[0].suit
        )
        trump_cards = [card for card in played_cards if card.suit == trump_suit]
        trump_cards.sort(key=lambda x: x.strength, reverse=True)

        winning_card = trump_cards[0]

        winning_card_idx = played_cards.index(winning_card)
        winning_player = self.turn_order()[winning_card_idx]

        # in Briscola, the winner plays next, but in online mode it's always the same shown user
        self.active_player = winning_player
        if self.active_player.is_person and not self.online:
            self.shown_player = self.active_player

        # and the person before the winner is the 'dealer'
        next_dealer_idx = winning_card_idx - 1 if winning_card_idx != 0 else -1
        self.dealer = self.turn_order()[next_dealer_idx]

        return winning_card, winning_player

    def end_turn(self) -> BriscolaTurnWinner:
        winning_card, self.last_winner = self.get_winning_card()
        earned_pts = self.calculate_points(self.active_pile.cards)
        self.last_winner.score += earned_pts

        losing_cards = [card for card in self.active_pile.cards if card != winning_card]

        self.clear_pile()
        self.fill_hands()

        logger.debug(", ".join(f"{player} has {player.score}pts" for player in self.players))

        return BriscolaTurnWinner(
            winning_card=winning_card,
            winning_player=self.last_winner,
            earned_pts=earned_pts,
            losing_cards=losing_cards,
        )

    def to_dict(self) -> dict:
        return {
            "table_settings": self.table_settings.to_dict(),
            "players": [player.to_dict() for player in self.players],
            "deck": self.deck.to_dict(),
            "briscola": {
                "suit": self.briscola.to_dict() if self.briscola is not None else None,
                "card": self.briscola_card.to_dict() if self.briscola_card is not None else None,
            },
            "pile": self.active_pile.to_dict(),
            "dealer": self.dealer.to_dict(),
            "active_player": self.active_player.to_dict(),
            "shown_player": self.shown_player.to_dict(),
            "game_ongoing": self.game_ongoing,
            "turn_order": [player.to_dict() for player in self.turn_order()],
            "last_winner": self.last_winner.to_dict() if self.last_winner is not None else None,
            "online": self.online,
        }

from typing import Callable, Final

from briscola.card import BriscolaCard
from briscola.deck import BriscolaDeck
from briscola.pile import BriscolaPile
from briscola.player import BriscolaPlayer
from card_game.cards.card import Card
from card_game.cards.suits import Suit
from card_game.game_client import CardGame
from card_game.table.player import PlayerColor
from card_game.table.table_settings import TableSettings
from settings.game_settings import CARDS_IN_HAND


class BriscolaGame(CardGame):
    briscola: Suit | None = None
    briscola_card: BriscolaCard | None = None
    max_cards_in_hand: int = 3
    active_pile: BriscolaPile = BriscolaPile(cards=[], face_up=True)
    win_condition: Final = 60

    def __init__(
        self,
        table_settings: TableSettings,
        computer_logic_override: tuple[Callable, ...] = (),
        computer_skill_level: int = 10,
        first_dealer: int | None = -1,
    ):
        self.computer_logic_override = computer_logic_override
        self.computer_skill_level = computer_skill_level
        super().__init__(
            table_settings=table_settings, deck=BriscolaDeck(), first_dealer=first_dealer
        )

    def __repr__(self) -> str:
        return f"Briscola Card: {self.briscola_card}\n" f"----\n" f"{super().__repr__()}"

    def deal_hands(self, cards_in_hand: int, change_dealers: bool = True) -> list[list[Card]]:
        # if briscola_card hasn't been set yet, then draw and set the briscola card first
        if self.briscola_card is None:
            self.briscola_card = self.deck.draw()
            self.briscola = self.briscola_card.suit
            # briscola card should be treated as the last card of the generics
            self.deck.cards.insert(0, self.briscola_card)
        return super().deal_hands(cards_in_hand=cards_in_hand, change_dealers=change_dealers)

    def fill_hands(self, max_cards_in_hand: int | None = None) -> None:
        return self.deck.fill_hands(
            players=self.players,
            max_cards_in_hand=self.max_cards_in_hand or max_cards_in_hand,
        )

    def play_card(self, player: BriscolaPlayer, card: BriscolaCard) -> None:
        player.hand.cards.remove(card)
        self.active_pile.cards.append(card)

    @property
    def game_ongoing(self) -> bool:
        no_winner = max(player.score for player in self.players) <= self.win_condition
        players_have_cards = max(len(player.hand.cards) for player in self.players) > 0

        return no_winner and players_have_cards

    def reset_game(self) -> None:
        self.deck = BriscolaDeck()
        self.briscola, self.briscola_card = None, None
        self.active_pile.clear_pile()
        self.players = self.create_players(self.table_settings.player_count)
        self.dealer = self.players[-1]
        self.active_player = self.players[0]
        self.deal_hands(cards_in_hand=CARDS_IN_HAND, change_dealers=False)

    def create_players(self, player_count: int) -> list[BriscolaPlayer]:
        colors = list(PlayerColor)
        players = [
            BriscolaPlayer(player_num=num + 1, color=colors[num]) for num in range(player_count)
        ]
        for computer_idx in range(0, self.table_settings.computer_count):
            computer = players[-(computer_idx + 1)]
            computer.is_person = False

        if self.table_settings.computer_count > 0:
            self.set_computer_logic(computers=players[-self.table_settings.computer_count :])

        return players

    def set_computer_logic(self, computers: list[BriscolaPlayer]) -> None:
        for idx, computer in enumerate(computers):
            computer.is_person = False
            computer.skill_level = self.computer_skill_level

            # set computer logic as the same idx a the override, or the first if there's no matching override
            try:
                computer.computer_logic_override = self.computer_logic_override[idx]
            except IndexError:
                computer.computer_logic_override = self.computer_logic_override[0]

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
            "game_ongoing": self.game_ongoing,
        }

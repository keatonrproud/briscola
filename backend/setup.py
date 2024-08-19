from typing import Callable

from briscola.client import BriscolaGame
from card_game.cards.card import Card
from card_game.table.table_settings import Direction, TableSettings
from settings.game_settings import CARDS_IN_HAND, PLAY_DIRECTION


def create_table_settings(
    player_count: int,
    play_direction: Direction = PLAY_DIRECTION,
    computer_count: int = 0,
) -> TableSettings:
    return TableSettings(
        player_count=player_count, turn_direction=play_direction, computer_count=computer_count
    )


def create_game(
    table_settings: TableSettings,
    logic_override: tuple[Callable, ...] = (),
    first_dealer: int | None = -1,
) -> BriscolaGame:
    return BriscolaGame(
        table_settings=table_settings,
        computer_logic_override=logic_override,
        first_dealer=first_dealer,
    )


def deal_hands(game: BriscolaGame) -> list[list[Card]]:
    return game.deal_hands(cards_in_hand=CARDS_IN_HAND, change_dealers=False)


def create_game_and_deal(
    player_count: int,
    play_direction: Direction = PLAY_DIRECTION,
    computer_count: int = 0,
    logic_override: tuple[Callable, ...] = (),
    first_dealer: int | None = -1,
) -> BriscolaGame:
    table_settings = create_table_settings(
        player_count=player_count, play_direction=play_direction, computer_count=computer_count
    )
    game = create_game(
        table_settings=table_settings, logic_override=logic_override, first_dealer=first_dealer
    )
    deal_hands(game=game)

    return game

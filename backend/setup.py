from briscola.client import BriscolaGame
from briscola.player import BriscolaPlayer
from card_game.cards.card import Card
from card_game.table.table_settings import Direction, TableSettings
from settings.game_settings import CARDS_IN_HAND


def create_table_settings(player_count: int, play_direction: Direction) -> TableSettings:
    return TableSettings(player_count, play_direction)


def create_players(player_count: int) -> list[BriscolaPlayer]:
    return [BriscolaPlayer(player_num=num + 1) for num in range(player_count)]


def create_game(table_settings: TableSettings, players: list[BriscolaPlayer]) -> BriscolaGame:
    return BriscolaGame(table_settings=table_settings, players=players)


def deal_hands(game: BriscolaGame) -> list[list[Card]]:
    return game.deal_hands(cards_in_hand=CARDS_IN_HAND, change_dealers=False)


def create_game_and_deal(player_count: int, play_direction: Direction) -> BriscolaGame:
    table_settings = create_table_settings(player_count=player_count, play_direction=play_direction)
    players = create_players(table_settings.player_count)
    game = create_game(table_settings=table_settings, players=players)
    deal_hands(game=game)

    return game

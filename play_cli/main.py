from backend.setup import create_game_and_deal, create_table_settings
from play_cli.cli_logic import cli_get_player_count, cli_play_game
from settings.game_settings import PLAY_DIRECTION

if __name__ == "__main__":
    table_settings = create_table_settings(cli_get_player_count(), PLAY_DIRECTION)
    briscola_game = create_game_and_deal(table_settings.player_count, PLAY_DIRECTION)

    cli_play_game(game=briscola_game)

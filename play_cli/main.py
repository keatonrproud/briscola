from play_cli.cli_logic import cli_play_game, cli_setup_game

if __name__ == "__main__":
    game = cli_setup_game()

    cli_play_game(game=game)

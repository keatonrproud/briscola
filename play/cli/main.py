from src.backend import basic_choice
from play.cli.cli_client import BriscolaCLI

if __name__ == "__main__":
    game = BriscolaCLI(computer_count=1, computer_logic_override=(basic_choice,))
    game.play_game()

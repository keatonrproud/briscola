from backend.setup import create_game_and_deal, create_table_settings
from backend.turn import end_turn
from briscola.client import BriscolaGame
from settings.game_settings import PLAY_DIRECTION


def web_get_player_count() -> int:
    # response = input(f"Player count (2): \n")
    # if response not in "2":
    #     input("The player count must be 2. Input your player count: \n")
    # else:
    #     return int(response)
    return 2


def web_setup_game() -> BriscolaGame:
    table_settings = create_table_settings(web_get_player_count(), PLAY_DIRECTION)
    game = create_game_and_deal(table_settings.player_count, PLAY_DIRECTION)

    return game


def web_play_card(card_idx: int, game: BriscolaGame) -> None:
    card_to_play = game.active_player.hand.cards[card_idx]
    game.play_card(game.active_player, card_to_play)

    if game.active_player == game.turn_order[-1]:
        end_turn(game)
    else:
        current_player_idx = game.turn_order.index(game.active_player)
        next_player_idx = (
            current_player_idx + 1 if current_player_idx + 1 != len(game.turn_order) else 0
        )
        game.active_player = game.turn_order[next_player_idx]

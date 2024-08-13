from dataclasses import dataclass
from typing import Callable

from briscola.card import BriscolaCard
from briscola.client import BriscolaGame
from briscola.player import BriscolaPlayer


@dataclass
class BriscolaTurnWinner:
    winning_card: BriscolaCard
    winning_player: BriscolaPlayer
    earned_pts: int


def fill_hands(game: BriscolaGame) -> None:
    game.fill_hands()


def end_turn(game: BriscolaGame) -> BriscolaTurnWinner:
    winning_card, winning_player = get_winning_card(game)
    earned_pts = calculate_points(game.active_pile.cards)
    winning_player.score += earned_pts

    print("cards played: ", game.active_pile.cards)
    print("winning card: ", winning_card)
    print("winning player: Player ", winning_player.player_num)
    print("earned points: ", earned_pts)

    clear_pile(game)
    fill_hands(game)

    return BriscolaTurnWinner(winning_card, winning_player, earned_pts)


def calculate_points(captured_cards: list[BriscolaCard]) -> int:
    return sum(card.points for card in captured_cards)


def clear_pile(game: BriscolaGame) -> None:
    game.active_pile.clear_pile()


def get_winning_card(game: BriscolaGame) -> tuple[BriscolaCard, BriscolaPlayer]:
    played_cards = game.active_pile.cards
    trump_suit = (
        game.briscola
        if len([card for card in played_cards if card.suit == game.briscola])
        else played_cards[0].suit
    )
    trump_cards = [card for card in played_cards if card.suit == trump_suit]
    trump_cards.sort(key=lambda x: x.strength, reverse=True)

    winning_card = trump_cards[0]

    turn_order = game.get_turn_order()
    winning_card_idx = played_cards.index(winning_card)
    winning_player = turn_order[winning_card_idx]

    # In Briscola, the winner plays next. So the person before the winner is the 'dealer'
    next_dealer_idx = winning_card_idx - 1 if winning_card_idx != 0 else 0
    game.dealer = turn_order[next_dealer_idx]

    return winning_card, winning_player


def play_card(player: BriscolaPlayer, card: BriscolaCard, game: BriscolaGame) -> BriscolaCard:
    game.play_card(player, card)
    return card


def start_turn(game: BriscolaGame, choose_card_method: Callable) -> None:
    for player in game.get_turn_order():
        played_card = choose_card_method(game=game, player=player)
        play_card(player=player, card=played_card, game=game)


def play_turn(game: BriscolaGame, choose_card_method: Callable) -> BriscolaTurnWinner:
    start_turn(game=game, choose_card_method=choose_card_method)
    return end_turn(game=game)

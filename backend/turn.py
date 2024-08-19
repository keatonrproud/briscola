from dataclasses import dataclass
from random import choice
from typing import Callable

from backend.computer_logic.basic import basic_choice
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

    game.last_winner = winning_player

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

    winning_card_idx = played_cards.index(winning_card)
    winning_player = game.turn_order()[winning_card_idx]

    # in Briscola, the winner plays next...
    game.active_player = winning_player

    # and the person before the winner is the 'dealer'
    next_dealer_idx = winning_card_idx - 1 if winning_card_idx != 0 else -1
    game.dealer = game.turn_order()[next_dealer_idx]

    return winning_card, winning_player


def play_card(player: BriscolaPlayer, card: BriscolaCard, game: BriscolaGame) -> BriscolaCard:
    game.play_card(player, card)
    return card


def start_turn(game: BriscolaGame, choose_card_method: Callable) -> None:
    for player in game.turn_order():
        game.active_player = player
        if player.is_person:
            played_card = choose_card_method(game=game, player=player)
        else:
            chosen_idx = play_card_computer(game=game, cards=player.hand.cards)
            played_card = game.active_player.hand.cards[chosen_idx]
        play_card(player=player, card=played_card, game=game)


def play_turn(game: BriscolaGame, choose_card_method: Callable) -> BriscolaTurnWinner:
    start_turn(game=game, choose_card_method=choose_card_method)
    return end_turn(game=game)


def play_card_computer(
    game: BriscolaGame,
    cards: list[BriscolaCard],
) -> int:

    random_choice = choice(range(len(cards)))
    # (1 - skill_level) * 10 is the percent chance of computer choosing a card randomly
    if choice(range(9)) >= game.computer_skill_level:
        return random_choice

    if len(game.players) > 2:
        raise NotImplementedError()

    return (
        basic_choice(game=game, cards=cards)
        if game.active_player.computer_logic_override is None
        else game.active_player.computer_logic_override(game=game, cards=cards)
    )

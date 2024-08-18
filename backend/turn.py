from dataclasses import dataclass
from random import choice
from typing import Callable

from briscola.card import BriscolaCard
from briscola.card_settings import BriscolaCardNumber
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
            played_card = choice(player.hand.cards)
        play_card(player=player, card=played_card, game=game)


def play_turn(game: BriscolaGame, choose_card_method: Callable) -> BriscolaTurnWinner:
    start_turn(game=game, choose_card_method=choose_card_method)
    return end_turn(game=game)


def computer_choice_logic(game: BriscolaGame, cards: list[BriscolaCard]) -> int:
    if len(game.players) > 2:
        raise NotImplementedError()

    briscola = game.briscola

    aces_and_threes = (BriscolaCardNumber.ACE, BriscolaCardNumber.THREE)

    # if computer is first
    if not game.active_pile.cards:
        # have a low non-briscola card, play the worst card
        if bad_card_idx := next(
            (idx for idx, card in enumerate(cards) if card.strength < 8 and card.suit != briscola),
            None,
        ):
            return bad_card_idx

        # have any cards not worth any points
        if zero_card_idx := next(
            (idx for idx, card in enumerate(cards) if card.points == 0),
            None,
        ):
            return zero_card_idx

        # (if only 3s and As, then play briscola if possible)
        if high_briscola_idx := next(
            (idx for idx, card in enumerate(cards) if card.suit not in aces_and_threes),
            None,
        ):
            return high_briscola_idx

        return choice(range(len(cards)))

    # if you're second
    opp_card = game.active_pile.cards[0]

    # if comp has off-suit for points, and opp played offsuit lower, then play it now
    if offsuit_winner := next(
        (
            idx
            for idx, card in enumerate(cards)
            if card.points > opp_card.points
            and card.points > 0
            and opp_card.suit != briscola
            and card.suit == opp_card.suit
        ),
        None,
    ):
        return offsuit_winner

    # if you can take any A or 3, take it
    if opp_card.suit in aces_and_threes:
        if opp_card.suit == briscola and (
            winning_idx := next(
                (
                    idx
                    for idx, card in enumerate(cards)
                    if card.suit == briscola and card.strength > opp_card.strength
                ),
                None,
            )
        ):
            return winning_idx
        elif winning_idx := next(
            (
                idx
                for idx, card in enumerate(cards)
                if card.suit == briscola
                or (card.suit == opp_card.suit and card.strength > opp_card.strength)
            ),
            None,
        ):
            return winning_idx

    # if it's a low card, and you can play off, play off
    if opp_card.points == 0:
        if opp_card.suit == briscola:
            if bad_not_briscola := next(
                (
                    idx
                    for idx, card in enumerate(cards)
                    if card.suit != briscola and card.points == 0
                ),
                None,
            ):
                return bad_not_briscola
            if worse_briscola := next(
                (idx for idx, card in enumerate(cards) if card.points == 0), None
            ):
                return worse_briscola
        elif opp_card.suit != briscola:
            if bad_losing_suit := next(
                (
                    idx
                    for idx, card in enumerate(cards)
                    if card.suit not in {briscola, opp_card.suit} and card.points == 0
                ),
                None,
            ):
                return bad_losing_suit
            if bad_same_suit := next(
                (
                    idx
                    for idx, card in enumerate(cards)
                    if card.suit == opp_card.suit and card.points == 0
                ),
                None,
            ):
                return bad_same_suit

    # otherwise, random
    return choice(range(len(cards)))

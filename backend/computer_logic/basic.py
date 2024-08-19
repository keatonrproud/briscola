from random import choice

from briscola.card import BriscolaCard
from briscola.card_settings import BriscolaCardNumber
from briscola.client import BriscolaGame


def basic_choice(game: BriscolaGame, cards: list[BriscolaCard]) -> int:

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
    return random_choice

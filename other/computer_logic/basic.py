from random import choice

from card_games.briscola.card import BriscolaCard
from card_games.briscola.card_settings import BriscolaCardNumber
from card_games.general.cards.suits import Suit
from card_games.general.table.pile import Pile


def basic_choice(briscola: Suit, active_pile: Pile, cards: list[BriscolaCard]) -> int:
    aces_and_threes = (BriscolaCardNumber.ACE, BriscolaCardNumber.THREE)

    print(f"points: {[card.points for card in cards]}")
    print(f"strengths: {[card.strength for card in cards]}")
    # if computer is first
    if not active_pile.cards:
        # have a low non-briscola card, play the worst card
        if (
            bad_card_idx := next(
                (
                    idx
                    for idx, card in enumerate(cards)
                    if card.points == 0 and card.suit != briscola
                ),
                None,
            )
        ) is not None:
            print("play bad card idx")
            return bad_card_idx

        # play a low pt non-briscola
        if (
            low_pt_non_briscola_idx := next(
                (
                    idx
                    for idx, card in enumerate(cards)
                    if card.points < 10 and card.suit != briscola
                ),
                None,
            )
        ) is not None:
            print("low pt non briscola")
            return low_pt_non_briscola_idx

        # have any briscola not worth any points
        if (
            zero_pt_briscola := next(
                (idx for idx, card in enumerate(cards) if card.points == 0),
                None,
            )
        ) is not None:
            print("zero pt briscola idx")
            return zero_pt_briscola

        # (if only 3s and As, then play briscola if possible)
        if (
            high_briscola_idx := next(
                (idx for idx, card in enumerate(cards) if card.suit not in aces_and_threes),
                None,
            )
        ) is not None:
            print("high briscola idx")
            return high_briscola_idx

        # otherwise, random of the non-ace-or-three cards
        if (
            non_ace_three := next(
                (idx for idx, card in enumerate(cards) if card.number not in aces_and_threes), None
            )
        ) is not None:
            print("random non ace or three")
            return non_ace_three

        print("random card")
        return choice(range(len(cards)))

    # if you're second
    opp_card = active_pile.cards[0]

    # if comp has off-suit for points, and opp played offsuit lower, then play it now
    if (
        offsuit_winner := next(
            (
                idx
                for idx, card in enumerate(cards)
                if card.strength > opp_card.strength
                and card.points > 0
                and opp_card.suit != briscola
                and card.suit == opp_card.suit
            ),
            None,
        )
    ) is not None:
        print("offsuit winner")
        return offsuit_winner

    # if you can take any A or 3, take it
    if opp_card.number in aces_and_threes:
        if (
            opp_card.suit == briscola
            and (
                winning_idx := next(
                    (
                        idx
                        for idx, card in enumerate(cards)
                        if card.suit == briscola and card.strength > opp_card.strength
                    ),
                    None,
                )
            )
            is not None
        ):
            print("take A or 3 briscola")
            return winning_idx
        elif (
            opp_card.suit != briscola
            and (
                winning_idx := next(
                    (
                        idx
                        for idx, card in enumerate(cards)
                        if card.suit == briscola
                        or (card.suit == opp_card.suit and card.strength > opp_card.strength)
                    ),
                    None,
                )
            )
            is not None
        ):
            print("take A or 3 non briscola")
            return winning_idx

    # if you can win points with a non-ace-or-three card, do it
    if (
        opp_card.points > 0
        and (
            non_ace_three_briscola_idx := next(
                (
                    idx
                    for idx, card in enumerate(cards)
                    if card.points < 10
                    and (card.suit == opp_card.suit or card.suit == briscola)
                    and card.strength > opp_card.strength
                ),
                None,
            )
        )
        is not None
    ):
        print("non ace three briscola")
        return non_ace_three_briscola_idx

    # if it's a low card, and you can play off, play off
    if opp_card.points == 0:
        if opp_card.suit == briscola:
            if (
                bad_not_briscola := next(
                    (
                        idx
                        for idx, card in enumerate(cards)
                        if card.suit != briscola and card.points == 0
                    ),
                    None,
                )
            ) is not None:
                print("bad not briscola")
                return bad_not_briscola
            if (
                worse_briscola := next(
                    (idx for idx, card in enumerate(cards) if card.points == 0), None
                )
            ) is not None:
                print("worse briscola")
                return worse_briscola
        elif opp_card.suit != briscola:
            if (
                bad_losing_suit := next(
                    (
                        idx
                        for idx, card in enumerate(cards)
                        if card.suit not in {briscola, opp_card.suit} and card.points == 0
                    ),
                    None,
                )
            ) is not None:
                print("bad losing suit")
                return bad_losing_suit

            if (
                bad_same_suit := next(
                    (
                        idx
                        for idx, card in enumerate(cards)
                        if card.suit == opp_card.suit and card.points == 0
                    ),
                    None,
                )
            ) is not None:
                print("bad same suit")
                return bad_same_suit

    if (
        card_worth_no_points := next(
            (idx for idx, card in enumerate(cards) if card.points == 0), None
        )
    ) is not None:
        print("card worth no points")
        return card_worth_no_points

    # otherwise, random
    return choice(range(len(cards)))

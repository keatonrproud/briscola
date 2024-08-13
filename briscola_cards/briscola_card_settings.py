from enum import auto
from card_game.cards.numbers import CardNumber
from card_game.cards.suits import COIN, CUP, CLUB, SWORD
from collections import namedtuple

SUITS = (COIN, CLUB, CUP, SWORD)


class BriscolaCardNumber(CardNumber):
    ACE = auto()
    TWO = auto()
    THREE = auto()
    FOUR = auto()
    FIVE = auto()
    SIX = auto()
    SEVEN = auto()
    JACK = auto()
    SOLDIER = auto()
    KING = auto()


BriscolaCardInfo = namedtuple("BriscolaCardInfo", ["strength", "points"])
CARD_INFOS = {
    BriscolaCardNumber.ACE: BriscolaCardInfo(strength=12, points=11),
    BriscolaCardNumber.THREE: BriscolaCardInfo(strength=11, points=10),
    BriscolaCardNumber.KING: BriscolaCardInfo(strength=10, points=4),
    BriscolaCardNumber.SOLDIER: BriscolaCardInfo(strength=9, points=3),
    BriscolaCardNumber.JACK: BriscolaCardInfo(strength=8, points=2),
    BriscolaCardNumber.SEVEN: BriscolaCardInfo(strength=7, points=0),
    BriscolaCardNumber.SIX: BriscolaCardInfo(strength=6, points=0),
    BriscolaCardNumber.FIVE: BriscolaCardInfo(strength=5, points=0),
    BriscolaCardNumber.FOUR: BriscolaCardInfo(strength=4, points=0),
    BriscolaCardNumber.TWO: BriscolaCardInfo(strength=2, points=0),
}

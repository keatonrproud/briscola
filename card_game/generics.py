from typing import TypeVar

from card_game.cards.card import Card
from card_game.cards.deck import Deck
from card_game.table.player import Player

DECK = TypeVar("DECK", bound="Deck")
PLAYER = TypeVar("PLAYER", bound="Player")
CARD = TypeVar("CARD", bound="Card")

from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from card_games.general.cards.deck import Deck

DECK = TypeVar("DECK", bound="Deck")

from typing import TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from card_games.general.cards.deck import Deck

DECK = TypeVar("DECK", bound="Deck")

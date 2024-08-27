from typing import TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from card_games.general.cards.card import Card

CARD = TypeVar("CARD", bound="Card")

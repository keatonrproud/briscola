from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from card_games.general.cards.card import Card

CARD = TypeVar("CARD", bound="Card")

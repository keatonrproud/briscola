from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from card_games.general.table.player import Player

PLAYER = TypeVar("PLAYER", bound="Player")

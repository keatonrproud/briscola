from typing import TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from card_games.general.table.player import Player

PLAYER = TypeVar("PLAYER", bound="Player")

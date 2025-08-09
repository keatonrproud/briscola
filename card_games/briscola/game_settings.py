from enum import Enum
from card_games.general.table.table_settings import Direction

CARDS_IN_HAND: int = 3
PLAY_DIRECTION: Direction = Direction.CLOCKWISE


class TeamName(int, Enum):
    """Team names for Briscola's 4-player mode."""

    TEAM_1 = 1
    TEAM_2 = 2

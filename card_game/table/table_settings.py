from enum import Enum, auto


class Direction(Enum):
    CLOCKWISE = auto()
    COUNTER_CLOCKWISE = auto()

    def __repr__(self) -> str:
        return self.name


class TableSettings:
    def __init__(self, player_count: int, turn_direction: Direction):
        self.player_count = player_count
        self.turn_direction = turn_direction

    def __repr__(self) -> str:
        return (
            f"Player Count: {self.player_count}\n" f"Turn Direction: {self.turn_direction.name}\n"
        )

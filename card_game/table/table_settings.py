from enum import Enum, auto


class Direction(Enum):
    CLOCKWISE = auto()
    COUNTER_CLOCKWISE = auto()

    def __repr__(self) -> str:
        return self.name


class TableSettings:
    def __init__(self, player_count: int, turn_direction: Direction, computer_count: int = 0):
        self.player_count = player_count
        self.turn_direction = turn_direction
        self.computer_count = computer_count
        assert (
            self.computer_count <= self.player_count
        ), "There can't be more computers than total players!"

    def __repr__(self) -> str:
        return (
            f"Player Count: {self.player_count}\n" f"Turn Direction: {self.turn_direction.name}\n"
        )

    def to_dict(self) -> dict:
        return {
            "player_count": self.player_count,
            "turn_direction": self.turn_direction.value,
            "computer_count": self.computer_count,
        }

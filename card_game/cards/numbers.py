from enum import Enum


class CardNumber(Enum):
    def __repr__(self) -> str:
        return self.name

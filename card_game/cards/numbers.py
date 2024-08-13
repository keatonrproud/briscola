from enum import Enum, auto


class CardNumber(Enum):
    def __repr__(self):
        return self.name

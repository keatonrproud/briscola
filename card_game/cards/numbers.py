from enum import Enum


class CardNumber(Enum):
    def __repr__(self) -> str:
        return self.name

    def to_dict(self) -> dict:
        return {"name": self.name}

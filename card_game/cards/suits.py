class Suit:
    def __init__(self, name: str, symbol: str):
        self.name = name
        self.symbol = symbol

    def __repr__(self) -> str:
        return self.symbol


COIN = Suit("COIN", "🪙")
SWORD = Suit("SWORD", "🗡")
CLUB = Suit("CLUB", "🪵")
CUP = Suit("CUP", "🏆")

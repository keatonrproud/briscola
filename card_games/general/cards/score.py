class Score:
    def __init__(self, value: int = 0) -> None:
        self.value = value

    def increase_score(self, increment: int = 1) -> None:
        self.value += increment

    def decrease_score(self, increment: int = -1) -> None:
        self.value -= increment

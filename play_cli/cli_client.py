from subprocess import call
from time import sleep
from typing import Callable

from briscola.card import BriscolaCard
from briscola.client import BriscolaGame, BriscolaTurnWinner
from briscola.player import BriscolaPlayer
from logging_config import build_logger

logger = build_logger(__name__)


class BriscolaCLI(BriscolaGame):

    def __init__(
        self,
        computer_count: int = 0,
        computer_logic_override: tuple[Callable, ...] = (),
        computer_skill_level: int = 10,
        first_dealer: int | None = -1,
    ):
        super().__init__(
            computer_count=computer_count,
            computer_logic_override=computer_logic_override,
            computer_skill_level=computer_skill_level,
            first_dealer=first_dealer,
        )

    @staticmethod
    def get_player_count() -> int:
        # response = input(f"Player count (2): \n")
        # if response not in "2":
        #     input("The player count must be 2. Input your player count: \n")
        # else:
        #     return int(response)
        return 2

    def announce_briscola(self) -> None:
        print(f"Briscola: {self.briscola_card}\n")

    def announce_played_cards(self) -> None:
        print(f"PILE: {self.active_pile}\n")

    def announce_game_state(self) -> None:
        print(f"{len(self.deck.cards)}🃏 remain")
        print("       ".join([f"{player}: {player.score}pts" for player in self.players]))
        print("----------------\n")

    def announce_scores(self, turn_winner: BriscolaTurnWinner) -> None:
        winning_card, winner, pts, losing_cards = (
            turn_winner.winning_card,
            turn_winner.winning_player,
            turn_winner.earned_pts,
            turn_winner.losing_cards,
        )

        print(
            f"Winner: {winner} with a {winning_card} vs {', '.join([card.__repr__() for card in losing_cards])}"
        )
        if pts != 0:
            print(f"{winner} went from {winner.score - pts} --> {winner.score}pts")
        else:
            print(f"{winner} stays at {winner.score}")
        print("=========================================\n")

    def announce_winner(self) -> None:
        max_score = max(player.score for player in self.players)
        try:
            winner = next(player for player in self.players if player.score > self.win_condition)
            print(f"{winner} wins with {winner.score} points!")
        except StopIteration:
            tied_players = [f"{player}" for player in self.players if player.score == max_score]
            print(f"The game ends with {' and '.join(tied_players)} having {max_score} points!")

    def choose_card(self, player: BriscolaPlayer) -> BriscolaCard:
        self.announce_game_state()
        self.announce_briscola()
        sleep(0.25)

        if self.active_pile.cards:
            self.announce_played_cards()

        print(f"{player}\n{player.hand}")
        while True:
            try:
                choice = int(input("Choose a card by inputting the number you want to play: ")) - 1
                assert choice in range(len(player.hand.cards))
            except ValueError:
                print("You must respond with a whole number!")
            except AssertionError:
                print("The number chosen must align with a card in the Player's hand.")
            else:
                break

        call("clear")
        return player.hand.cards[choice]

    def start_turn(self) -> None:
        for player in self.turn_order():
            self.active_player = player
            if self.active_player.is_person and not self.fixed_shown_player:
                self.shown_player = self.active_player
            logger.debug(f"{player} has {player.hand.cards}")
            if player.is_person:
                played_card = self.choose_card(player=player)
            else:
                chosen_idx = self.play_card_computer(cards=player.hand.cards)
                played_card = self.active_player.hand.cards[chosen_idx]

            logger.debug(f"{player} played {played_card}")
            self.play_card(player=player, card=played_card)

    def play_turn(self) -> BriscolaTurnWinner:
        self.start_turn()
        return self.end_turn()

    def play_game(self) -> None:
        self.deal_hands(change_dealers=False)
        while self.game_ongoing:
            turn_winner = self.play_turn()
            self.announce_scores(turn_winner)
        else:
            self.announce_winner()

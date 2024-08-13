from card_game.cards.card import Card
from card_game.cards.deck import Deck
from card_game.table.player import Player
from card_game.table.table_settings import TableSettings


class CardGame:
    def __init__(
        self,
        table_settings: TableSettings,
        deck: Deck,
        players: list[Player],
        first_dealer: Player = None,
    ):
        self.table_settings = table_settings
        self.deck = deck
        self.players = players
        self.first_dealer = first_dealer
        self.dealer = first_dealer if first_dealer is not None else self.players[-1]

    def __repr__(self):
        game_info = f"{self.table_settings}{self.deck}"
        player_info = "".join([str(player) for player in self.players])
        return game_info + "\n----\n" + player_info

    def get_turn_order(self) -> list[Player]:
        dealer_idx = self.players.index(self.dealer)
        first_player_idx = dealer_idx + 1 if dealer_idx < len(self.players) - 1 else 0
        return self.players[first_player_idx:] + self.players[:first_player_idx]

    @property
    def scores(self) -> list[int]:
        return [player.score for player in self.players]

    def deal_hands(
        self, cards_in_hand: int, change_dealers: bool = True
    ) -> list[list[Card]]:
        if change_dealers:
            self.change_dealers()
        return self.deck.deal(players=self.players, cards_in_hand=cards_in_hand)

    def fill_hands(self, max_cards_in_hand: int) -> None:
        return self.deck.fill_hands(
            players=self.players, max_cards_in_hand=max_cards_in_hand
        )

    def draw_card(self, player: Player, draw_count: int = 0):
        player.hand.cards += self.deck.draw_cards(draw_count=draw_count)

    def change_dealers(self):
        dealer_index = self.players.index(self.dealer)
        if dealer_index + 1 == len(self.players):
            self.dealer = self.players[0]
        else:
            self.dealer = self.players[dealer_index + 1]

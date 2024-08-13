from card_game.cards.deck import Deck
from briscola_cards.briscola_card import BriscolaCard
from briscola_cards.briscola_card_settings import SUITS, CARD_INFOS, BriscolaCardNumber

def generate_cards() -> list[BriscolaCard]:
    for suit in SUITS:
        for number in BriscolaCardNumber:
            yield BriscolaCard(number=number, suit=suit, card_info=CARD_INFOS[number])

BRISCOLA_DECK = Deck(deck_type="BRISCOLA", card_set=list(generate_cards()))

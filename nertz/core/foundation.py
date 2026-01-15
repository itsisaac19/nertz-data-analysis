import random
from typing import List
from nertz.models.cards import PlayingCard


"""Foundation piles start with an ace and build up by suit, so
we will construct identifiers based on player index and suit."""
class Foundation:
    def __init__(self, card: PlayingCard, player_index: int):
        if not card.rank == "A":
            raise ValueError("Initial card must be an ace.")
        
        self.suit = card.suit
        self.cards : List[PlayingCard] = [card]
        self.player_index = player_index
        self.identifier = f"foundation_{player_index}_{self.suit}"

    def top(self) -> PlayingCard:
        return self.cards[-1]

    def add_card(self, card: PlayingCard) -> None:
        self.cards.append(card)

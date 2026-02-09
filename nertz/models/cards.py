"""Card-related data types and constants."""
from typing import List, Literal
from dataclasses import dataclass

from nertz.engine.constants import PlayerIndex

SUIT = Literal["spades", "clubs", "hearts", "diamonds"]
SUITS: List[str] = ["spades", "clubs", "hearts", "diamonds"]
RANK = Literal["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
RANKS: List[str] = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

@dataclass(frozen=True)
class PlayingCard:
    """Immutable playing card."""
    suit: SUIT
    rank: RANK
    player_index: PlayerIndex
    
    def __str__(self) -> str:
        return f"{self.rank} of {self.suit}"
    
    def equals(self, other: 'PlayingCard') -> bool:
        return (self.suit == other.suit and
                self.rank == other.rank and
                self.player_index == other.player_index)
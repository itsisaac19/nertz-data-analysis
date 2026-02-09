from typing import TypeAlias, Literal
from enum import Enum


FoundationIdentifier : TypeAlias = str
"""Identifier for a foundation, formatted as: foundation_[PINDEX]_[SUIT]"""
PlayerIndex : TypeAlias = int
"""Index of a player, starting from 0 up to player_count - 1"""

RIVER_SLOT_COUNT = 4
MAX_DISTANCE_PENALTY_FACTOR = 0.3
NERTZ_UNIQUE_FOUNDATION_BONUS_MULTIPLIER = 20.0
TOTAL_RANKS = 13
RED_SUITS = {"hearts", "diamonds"}
BLACK_SUITS = {"spades", "clubs"}

class MoveType(Enum):
    """All the possible move types in Nertz."""
    NERTZ_TO_FOUNDATION = "NertzToFoundation"
    RIVER_TO_FOUNDATION = "RiverToFoundation"
    DECK_TO_FOUNDATION  = "DeckToFoundation"
    DECK_TO_RIVER      = "DeckToRiver"
    NERTZ_TO_RIVER     = "NertzToRiver"
    RIVER_TO_RIVER     = "RiverToRiver"
    DECK_TO_DECK       = "DeckToDeck"  # Represents flipping into stream from deck


# Base priority weights per move type
MOVE_TYPE_WEIGHTS: dict[MoveType, float] = {
    MoveType.NERTZ_TO_FOUNDATION: 1.0,
    MoveType.NERTZ_TO_RIVER:      0.9,
    MoveType.RIVER_TO_FOUNDATION: 0.5,
    MoveType.DECK_TO_FOUNDATION:  0.4,
    MoveType.DECK_TO_RIVER:       0.3,
    MoveType.RIVER_TO_RIVER:      0.3,

    # We will use DECK_TO_DECK to represent the action 
    # of flipping into the stream from the deck.
    # This is a very low priority move.
    MoveType.DECK_TO_DECK:        0.1, 
}

LocationType: TypeAlias = Literal[
    "NertzPile",
    "RiverPile",
    "DeckPile",
    "FoundationPile",
]
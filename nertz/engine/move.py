from __future__ import annotations
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from nertz.models.cards import PlayingCard, RANKS
from nertz.engine.constants import (
    LocationType,
    MoveType,
    MOVE_TYPE_WEIGHTS,
    MAX_DISTANCE_PENALTY_FACTOR,
    NERTZ_UNIQUE_FOUNDATION_BONUS_MULTIPLIER,
    TOTAL_RANKS,
)
from nertz.engine.exceptions import MoveValidationError


@dataclass
class FoundationSummary:
    """Lightweight snapshot of a single foundation pile — just enough
    data for priority / strategic-bonus calculations."""
    identifier: str
    suit: str
    top_rank: str


@dataclass
class MoveContext:
    """Read-only context that a Move needs for priority calculation.

    Built once per turn by the engine / move generator, so that Move
    never depends on the full GameState.
    """
    foundations: Dict[str, FoundationSummary] = field(default_factory=dict)
    """Keyed by foundation identifier."""

    @classmethod
    def from_game_state(cls, game_state) -> MoveContext:
        """Create a MoveContext from a live GameState.

        Parameters
        ----------
        game_state
            A ``nertz.models.game.GameState`` instance.  The type is not
            annotated explicitly to avoid importing the models package
            (keeps this module dependency-light).
        """
        foundations: Dict[str, FoundationSummary] = {}
        for fid, foundation in game_state.foundations.items():
            foundations[fid] = FoundationSummary(
                identifier=foundation.identifier,
                suit=foundation.suit,
                top_rank=foundation.top().rank,
            )
        return cls(foundations=foundations)


@dataclass
class GameResult:
    """Results from a completed game."""
    winner: int
    turns_played: int
    final_scores: List[int]
    foundations_created: int
    game_duration_seconds: float


@dataclass
class Move:
    """Represents a single player move.

    Priority is calculated automatically in ``__post_init__`` using only
    the lightweight ``MoveContext`` — no reference to the full GameState.
    """
    player_index: int
    context: MoveContext
    source_pile: LocationType
    destination_pile: LocationType
    card: Optional[PlayingCard]
    distance: float
    move_type: MoveType
    _priority: float = field(default=0.0, init=False, repr=False)
    priority: float = field(default=0.0, init=False)
    foundation_identifier: Optional[str] = None
    """The foundation identifier the card is placed into, if applicable."""
    river_slot_source: Optional[int] = None
    """The river slot index the card is taken from, if applicable."""
    river_slot_destination: Optional[int] = None
    """The river slot index the card is placed into, if applicable."""

    # ------------------------------------------------------------------
    # Validation & priority
    # ------------------------------------------------------------------

    def __post_init__(self) -> None:
        self._validate_fields()
        self.priority = self._calculate_priority()

    def _validate_fields(self) -> None:
        """Raise ``MoveValidationError`` when required fields are missing."""
        if self.destination_pile == "FoundationPile" and not self.foundation_identifier:
            raise MoveValidationError(
                "foundation_identifier must be provided for FoundationPile moves"
            )
        if self.source_pile == "RiverPile" and self.river_slot_source is None:
            raise MoveValidationError(
                "river_slot_source must be provided for RiverPile source moves"
            )
        if self.destination_pile == "RiverPile" and self.river_slot_destination is None:
            raise MoveValidationError(
                "river_slot_destination must be provided for RiverPile destination moves"
            )

    def _calculate_priority(self) -> float:
        """Derive a priority score from base weight, distance and strategy."""
        base_weight = MOVE_TYPE_WEIGHTS.get(self.move_type, 0.5)

        # Closer moves score higher; distance ∈ [0, 1]
        distance_factor = 1.0 - (self.distance * MAX_DISTANCE_PENALTY_FACTOR)

        strategic_bonus = self._calculate_strategic_bonus()

        return base_weight * distance_factor + strategic_bonus

    def _calculate_strategic_bonus(self) -> float:
        """Extra priority for moves that are strategically valuable."""
        bonus = 0.0

        if self.card is None:
            return bonus

        # Bonus for moving a nertz card to a unique foundation
        if (
            self.source_pile == "NertzPile"
            and self.destination_pile == "FoundationPile"
        ):
            duplicate_foundation = any(
                fs.suit == self.card.suit
                and fs.identifier != self.foundation_identifier
                for fs in self.context.foundations.values()
            )
            if not duplicate_foundation:
                # Higher-ranked nertz cards are harder to play later when
                # the foundation is the only one of its suit.
                rank_weight = (RANKS.index(self.card.rank) + 1) / float(TOTAL_RANKS)
                bonus += rank_weight * NERTZ_UNIQUE_FOUNDATION_BONUS_MULTIPLIER

        return bonus
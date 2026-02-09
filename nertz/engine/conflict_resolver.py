from __future__ import annotations

from typing import Dict, List
from nertz.engine.constants import FoundationIdentifier
from nertz.engine.move import Move
from nertz.utils.logger import Logger


class ConflictResolver:
    """Resolves conflicts when multiple players target the same foundation.

    Conflicts only arise when two or more players attempt to place a card
    on the same foundation pile in the same turn.  Ace moves are exempt
    because they always create a *new* foundation.

    Resolution strategy (current):
        Sort competing moves by (-priority, distance, player_index) and
        accept only the highest-ranked move.  All others are discarded.
    """

    def __init__(self, logger: Logger):
        self.logger = logger

    def resolve(self, chosen_moves: List[Move]) -> List[Move]:
        """Separate conflicting foundation moves and return the final
        list of moves that should be executed.

        Parameters
        ----------
        chosen_moves : List[Move]
            Each player's single best move for this turn.

        Returns
        -------
        List[Move]
            The moves that should actually be executed (conflicts resolved).
        """
        executable_moves: List[Move] = []
        conflict_map: Dict[FoundationIdentifier, List[Move]] = {}

        for move in chosen_moves:
            if move.destination_pile != "FoundationPile":
                # Non-foundation moves never conflict
                executable_moves.append(move)
                continue

            if move.card.rank == "A":
                # Aces always create new foundations — no conflict
                executable_moves.append(move)
                continue

            dest_id = move.foundation_identifier
            if dest_id not in conflict_map:
                conflict_map[dest_id] = []
            conflict_map[dest_id].append(move)

        for foundation_id, foundation_moves in conflict_map.items():
            winner = self._resolve_foundation_conflict(foundation_id, foundation_moves)
            executable_moves.append(winner)

        return executable_moves

    def _resolve_foundation_conflict(self, foundation_id: FoundationIdentifier, moves: List[Move]) -> Move:
        """Pick the winning move for a single foundation.

        When only one move targets the foundation it wins automatically.
        Otherwise, moves are ranked by highest priority, then shortest
        distance, then lowest player index as a stable tiebreaker.
        """
        if len(moves) == 1:
            return moves[0]

        moves.sort(key=lambda m: (-m.priority, m.distance, m.player_index))
        winner = moves[0]
        discarded_count = len(moves) - 1

        self.logger.log(
            "Conflict on foundation %s. Accepted move by player %d "
            "(priority=%.2f, distance=%.2f). %d competing move(s) discarded."
            % (
                foundation_id,
                winner.player_index,
                winner.priority,
                winner.distance,
                discarded_count,
            ),
            level="INFO",
        )

        return winner
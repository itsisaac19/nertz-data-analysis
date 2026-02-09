from typing import List, Optional

from nertz.models.game import GameState, PlayerState
from nertz.engine.scoring import process_game_scores
from nertz.engine.exceptions import (
    GameNotStartedError,
    GameOverError,
)
from nertz.engine.move import Move
from nertz.engine.move_executor import MoveExecutor
from nertz.engine.conflict_resolver import ConflictResolver
from nertz.engine.move_generator import MoveGenerator

from nertz.utils.logger import Logger


"""Engine TODOs:"""
# TODO: Implement timeouts and asynchronous move calculations for players
# TODO: Implement scoring and end-game conditions
# TODO: Add unit tests for move priority calculations and conflict resolution
class NertzEngine:
    def __init__(self, player_count: int = 2):
        self.player_count = player_count
        self.game_state: GameState = GameState(player_count=player_count)
        self.turn_counter = 0
        self.logger = Logger()
        self.move_generator = MoveGenerator(self.game_state, self.logger)
        self.move_executor = MoveExecutor(self.game_state, self.logger)
        self.conflict_resolver = ConflictResolver(self.logger)

    def start_new_game(self) -> None:
        """Initialize a new game."""
        self.turn_counter = 0
        self.logger.log("Starting new game", level="INFO")

    def play_turn(self) -> None:
        """Simulate a single turn of the game.

        1. Each player's legal moves are generated.
        2. The best move per player is selected.
        3. Conflicts are resolved.
        4. Winning moves are executed.
        """
        if self.is_game_over():
            self.logger.log("Game over. Cannot play further turns.", level="WARNING")
            process_game_scores(self.game_state)
            raise GameOverError()

        self.turn_counter += 1
        self.logger.log(f"--- TURN {self.turn_counter} ---", level="INFO")

        chosen_moves = self._gather_player_moves()

        self.logger.log("Resolving conflicts and executing moves...", level="INFO")
        resolved_moves = self.conflict_resolver.resolve(chosen_moves)
        for move in resolved_moves:
            self.move_executor.execute(move)

    # ------------------------------------------------------------------
    # Turn helpers
    # ------------------------------------------------------------------

    def _gather_player_moves(self) -> List[Move]:
        """Generate legal moves for every player and pick each player's best."""
        chosen_moves: List[Move] = []

        for player in self.game_state.players:
            self._log_player_state(player)

            legal_moves = self.move_generator.calculate_legal_moves(player.player_index)
            self.logger.log_debug(
                f"Player {player.player_index} has {len(legal_moves)} legal moves."
            )
            self._log_legal_moves(legal_moves)

            best = self._select_best_move(legal_moves)
            if best:
                chosen_moves.append(best)
                self.logger.log(
                    "Chosen move: player=%d card=%s from=%s to=%s "
                    "priority=%.2f distance=%.2f"
                    % (
                        best.player_index,
                        best.card,
                        best.source_pile,
                        best.destination_pile,
                        best.priority,
                        best.distance,
                    ),
                    level="INFO",
                )

        return chosen_moves

    @staticmethod
    def _select_best_move(moves: List[Move]) -> Optional[Move]:
        """Return the move with the highest combined score, or ``None``."""
        best_move: Optional[Move] = None
        best_score = -1.0

        for move in moves:
            combined_score = move.priority + move.distance
            if combined_score > best_score:
                best_score = combined_score
                best_move = move

        return best_move

    # ------------------------------------------------------------------
    # Debug logging helpers
    # ------------------------------------------------------------------

    def _log_player_state(self, player: PlayerState) -> None:
        """Log the current river and stream state for a player."""
        self.logger.log_debug("-------------")

        self.logger.log_debug("[RIVER STATE]")
        for i, river_pile in enumerate(player.deck.cards_in_river):
            if river_pile:
                self.logger.log_debug(f"  River slot {i}: top card {river_pile[-1]}")
            else:
                self.logger.log_debug(f"  River slot {i}: <empty>")

        self.logger.log_debug("[STREAM STATE]")
        if player.deck.cards_in_stream:
            self.logger.log_debug(f"  Top stream card: {player.deck.get_top_stream_card()}")
        else:
            self.logger.log_debug("  Top stream card: <empty>")

    def _log_legal_moves(self, moves: List[Move]) -> None:
        """Log each legal move at debug level."""
        self.logger.log_debug("[LEGAL MOVES]")
        for move in moves:
            self.logger.log_debug(
                "  Move: card=%s from=%s to=%s priority=%.2f distance=%.2f"
                % (
                    move.card,
                    move.source_pile,
                    move.destination_pile,
                    move.priority,
                    move.distance,
                )
            )

    # ------------------------------------------------------------------
    # Game state checks
    # ------------------------------------------------------------------

    def is_game_over(self) -> bool:
        """Check if any player has emptied their Nertz pile."""
        for player in self.game_state.players:
            if len(player.deck.cards_in_nertz) == 0:
                self.logger.log(
                    f"Player {player.player_index} has emptied their Nertz pile. Game over!",
                    level="INFO",
                )
                return True
        return False
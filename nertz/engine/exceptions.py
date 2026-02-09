from typing import Optional


class NertzEngineError(Exception):
    """Base exception for all Nertz engine errors."""
    pass


class InvalidMoveError(NertzEngineError):
    """Raised when a move violates game rules or is otherwise illegal."""
    def __init__(self, message: str, player_index: Optional[int] = None):
        self.player_index = player_index
        prefix = f"Player {player_index}: " if player_index is not None else ""
        super().__init__(f"{prefix}{message}")


class CardMismatchError(InvalidMoveError):
    """Raised when the expected card at a pile location doesn't match the move's card."""
    def __init__(self, expected, actual, pile_name: str, player_index: Optional[int] = None):
        self.expected = expected
        self.actual = actual
        self.pile_name = pile_name
        super().__init__(
            f"Card mismatch at {pile_name}: expected {expected}, got {actual}",
            player_index=player_index,
        )


class InvalidPileError(InvalidMoveError):
    """Raised when a pile type or pile reference is invalid."""
    def __init__(self, pile_name: str, reason: str = "does not exist", player_index: Optional[int] = None):
        self.pile_name = pile_name
        super().__init__(
            f"Invalid pile '{pile_name}': {reason}",
            player_index=player_index,
        )


class MoveValidationError(InvalidMoveError):
    """Raised when a Move dataclass fails field validation in __post_init__."""
    pass


class GameNotStartedError(NertzEngineError):
    """Raised when an action is attempted before the game has been initialized."""
    def __init__(self):
        super().__init__("Game has not been started.")


class GameOverError(NertzEngineError):
    """Raised when an action is attempted after the game has ended."""
    def __init__(self):
        super().__init__("Game is over. Cannot play further turns.")
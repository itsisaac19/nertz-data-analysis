from __future__ import annotations
from typing import List, Optional

from nertz.models.game import GameState
from nertz.models.cards import PlayingCard, RANKS
from nertz.engine.layout import Point
from nertz.engine.constants import (
    LocationType,
    MoveType,
    RIVER_SLOT_COUNT,
    RED_SUITS,
)
from nertz.engine.exceptions import InvalidPileError
from nertz.engine.move import Move, MoveContext
from nertz.utils.logger import Logger


class MoveGenerator:
    """Generates all legal moves for a given player in the current game state."""

    def __init__(self, game_state: GameState, logger: Logger):
        self.game_state = game_state
        self.logger = logger

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def calculate_legal_moves(self, player_index: int) -> List[Move]:
        """Return every legal move available to the given player."""
        if not self.game_state:
            return []

        # Build context once — foundations don't change during move generation
        self._current_context = MoveContext.from_game_state(self.game_state)

        legal_moves: List[Move] = []

        self._add_nertz_moves(player_index, legal_moves)
        self._add_river_to_foundation_moves(player_index, legal_moves)
        self._add_river_to_river_moves(player_index, legal_moves)
        self._add_deck_moves(player_index, legal_moves)

        return legal_moves

    # ------------------------------------------------------------------
    # Individual move generators
    # ------------------------------------------------------------------

    def generate_river_move(
        self,
        player_index: int,
        card: PlayingCard,
        source_pile: LocationType,
    ) -> Optional[Move]:
        """Generate a move to a river slot if one is available."""
        if source_pile == "RiverPile":
            raise InvalidPileError(
                "RiverPile",
                reason="Do not use this method for river-to-river moves.",
                player_index=player_index,
            )

        player = self.game_state.players[player_index]
        distance = self._distance_player_to_river(player_index)

        def _build_river_move(river_slot_index: int) -> Move:
            move_type = (
                MoveType.DECK_TO_RIVER
                if source_pile == "DeckPile"
                else MoveType.NERTZ_TO_RIVER
            )
            return Move(
                player_index=player_index,
                context=self._current_context,
                source_pile=source_pile,
                destination_pile="RiverPile",
                river_slot_destination=river_slot_index,
                move_type=move_type,
                card=card,
                distance=distance,
            )

        for i in range(RIVER_SLOT_COUNT):
            if not player.deck.cards_in_river[i]:
                return _build_river_move(i)
            elif self._is_valid_solitaire_move(card, player.deck.cards_in_river[i][-1]):
                return _build_river_move(i)

        return None

    def generate_foundation_move(
        self,
        player_index: int,
        card: PlayingCard,
        source_pile: LocationType,
        river_slot_source_index: Optional[int] = None,
    ) -> Optional[Move]:
        """Generate a move to a foundation pile if one is available."""
        table = self.game_state.table
        player_pos = Point(*table.get_player_position(player_index))

        move_type: MoveType
        if source_pile == "NertzPile":
            move_type = MoveType.NERTZ_TO_FOUNDATION
        elif source_pile == "RiverPile":
            move_type = MoveType.RIVER_TO_FOUNDATION
        elif source_pile == "DeckPile":
            move_type = MoveType.DECK_TO_FOUNDATION
        else:
            raise InvalidPileError(
                source_pile,
                reason="Unsupported source pile for foundation move.",
                player_index=player_index,
            )

        def _build_foundation_move(foundation_id: str, foundation_pos: Point) -> Move:
            distance = table.distance_between(player_pos, foundation_pos)
            return Move(
                player_index=player_index,
                context=self._current_context,
                source_pile=source_pile,
                river_slot_source=river_slot_source_index,
                destination_pile="FoundationPile",
                foundation_identifier=foundation_id,
                move_type=move_type,
                card=card,
                distance=distance,
            )

        if card.rank == "A":
            foundation_id = f"foundation_{player_index}_{card.suit}"
            foundation_position = self.game_state.table.place_foundation(foundation_id)
            return _build_foundation_move(foundation_id, foundation_position)

        for foundation in self.game_state.foundations.values():
            if (
                card.suit == foundation.suit
                and card.rank == self._next_rank(foundation.top().rank)
            ):
                foundation_pos = Point(
                    *table.get_foundation_position(foundation.identifier)
                )
                return _build_foundation_move(foundation.identifier, foundation_pos)

        return None

    def generate_stream_flip_move(self, player_index: int) -> Optional[Move]:
        """Generate a move representing flipping cards from the deck into the stream."""
        return Move(
            player_index=player_index,
            context=self._current_context,
            source_pile="DeckPile",
            destination_pile="DeckPile",
            move_type=MoveType.DECK_TO_DECK,
            card=None,
            distance=0.0,
        )

    # ------------------------------------------------------------------
    # Private helpers — move category builders
    # ------------------------------------------------------------------

    def _add_nertz_moves(self, player_index: int, legal_moves: List[Move]) -> None:
        # ...existing code...
        player = self.game_state.players[player_index]
        if not player.deck.cards_in_nertz:
            return

        nertz_card = player.deck.top_nertz_card()
        if not nertz_card:
            return

        move = self.generate_foundation_move(player_index, nertz_card, "NertzPile")
        if move:
            legal_moves.append(move)
        else:
            move = self.generate_river_move(player_index, nertz_card, "NertzPile")
            if move:
                legal_moves.append(move)

    def _add_river_to_foundation_moves(
        self, player_index: int, legal_moves: List[Move]
    ) -> None:
        # ...existing code...
        player = self.game_state.players[player_index]
        for i in range(RIVER_SLOT_COUNT):
            current_river_pile = player.deck.cards_in_river[i]
            if not current_river_pile:
                continue
            river_card = current_river_pile[-1]
            move = self.generate_foundation_move(
                player_index, river_card, "RiverPile", river_slot_source_index=i
            )
            if move:
                legal_moves.append(move)

    def _add_river_to_river_moves(
        self, player_index: int, legal_moves: List[Move]
    ) -> None:
        # ...existing code...
        player = self.game_state.players[player_index]

        for i in range(RIVER_SLOT_COUNT):
            current_river_pile = player.deck.cards_in_river[i]
            if not current_river_pile:
                continue

            source_card = current_river_pile[0]
            for j in range(RIVER_SLOT_COUNT):
                if i == j:
                    continue
                dest_river_pile = player.deck.cards_in_river[j]
                if not dest_river_pile:
                    continue
                dest_card = dest_river_pile[-1]
                if self._is_valid_solitaire_move(source_card, dest_card):
                    distance = self._distance_player_to_river(player_index)

                    self.logger.log_debug(
                        "Legal RiverToRiver move: player=%d card=%s "
                        "from_slot=%d to_slot=%d distance=%.2f"
                        % (player_index, source_card, i, j, distance)
                    )

                    move = Move(
                        player_index=player_index,
                        context=self._current_context,
                        source_pile="RiverPile",
                        destination_pile="RiverPile",
                        river_slot_source=i,
                        river_slot_destination=j,
                        move_type=MoveType.RIVER_TO_RIVER,
                        card=source_card,
                        distance=distance,
                    )
                    legal_moves.append(move)

    def _add_deck_moves(self, player_index: int, legal_moves: List[Move]) -> None:
        # ...existing code...
        player = self.game_state.players[player_index]

        stream_flip_move = self.generate_stream_flip_move(player_index)
        if stream_flip_move:
            legal_moves.append(stream_flip_move)

        top_deck_card: Optional[PlayingCard] = player.deck.get_top_stream_card()
        if top_deck_card is None:
            return

        move = self.generate_river_move(player_index, top_deck_card, "DeckPile")
        if move:
            legal_moves.append(move)
        else:
            move = self.generate_foundation_move(
                player_index, top_deck_card, "DeckPile"
            )
            if move:
                legal_moves.append(move)

    # ------------------------------------------------------------------
    # Card rule helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _distance_player_to_river(player_index: int) -> float:
        # ...existing code...
        return 0.0

    @staticmethod
    def _next_rank(rank: str) -> str:
        # ...existing code...
        if rank not in RANKS:
            raise ValueError(f"Invalid rank: {rank}")
        index = RANKS.index(rank)
        return RANKS[index + 1] if index + 1 < len(RANKS) else ""

    @staticmethod
    def _is_opposite_color(card1: PlayingCard, card2: PlayingCard) -> bool:
        # ...existing code...
        return (card1.suit in RED_SUITS) != (card2.suit in RED_SUITS)

    @classmethod
    def _is_valid_solitaire_move(
        cls, source_card: PlayingCard, dest_card: PlayingCard
    ) -> bool:
        # ...existing code...
        return (
            cls._is_opposite_color(source_card, dest_card)
            and cls._next_rank(source_card.rank) == dest_card.rank
        )
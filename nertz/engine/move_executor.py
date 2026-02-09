from __future__ import annotations

from nertz.models.game import GameState, PlayerState
from nertz.engine.constants import MoveType
from nertz.engine.exceptions import (
    CardMismatchError,
    InvalidPileError,
    MoveValidationError,
)
from nertz.engine.move import Move
from nertz.utils.logger import Logger


class MoveExecutor:
    """Responsible for applying moves to the game state.

    Given a validated Move, this class mutates the GameState by:
    1. Placing the card in its destination pile.
    2. Removing the card from its source pile.
    """

    def __init__(self, game_state: GameState, logger: Logger):
        self.game_state = game_state
        self.logger = logger

    def execute(self, move: Move) -> None:
        """Execute a single move against the current game state."""
        self.logger.log(
            "Executing move: player=%d card=%s from=%s to=%s"
            % (
                move.player_index,
                move.card,
                move.source_pile,
                move.destination_pile,
            ),
            level="INFO",
        )
        player = self.game_state.players[move.player_index]

        if move.move_type == MoveType.DECK_TO_DECK:
            # Special case: flip into stream from deck
            player.deck.flip__into_stream()
            self.logger.log(
                f"Player {move.player_index} flipped cards into stream.",
                level="INFO",
            )
            return

        self._apply_destination_effects(move, player)
        self._apply_source_effects(move, player)

        self.logger.log_debug("Move executed successfully.")

    # ------------------------------------------------------------------
    # Destination effects
    # ------------------------------------------------------------------

    def _apply_destination_effects(self, move: Move, player: PlayerState) -> None:
        """Place the card in the destination pile."""
        if move.destination_pile == "FoundationPile":
            self._place_on_foundation(move, player)
        elif move.destination_pile == "RiverPile":
            self._place_on_river(move, player)
        # DeckPile and NertzPile are never a destination in the current ruleset

    def _place_on_foundation(self, move: Move, player: PlayerState) -> None:
        """Place a card onto a foundation pile (or create a new one for Aces)."""
        if move.card.rank == "A":
            self.game_state.create_foundation(move.card, move.player_index)
            player.deck.cards_in_lake.append(move.card)
        else:
            foundation_id = move.foundation_identifier
            foundation = self.game_state.foundations.get(foundation_id)
            if foundation:
                foundation.add_card(move.card)
                player.deck.cards_in_lake.append(move.card)
            else:
                raise InvalidPileError(
                    foundation_id,
                    reason="does not exist",
                    player_index=move.player_index,
                )

    def _place_on_river(self, move: Move, player: PlayerState) -> None:
        """Place a card into a river slot."""
        if move.river_slot_destination is None:
            raise MoveValidationError(
                "River slot destination index must be specified for RiverPile moves.",
                player_index=move.player_index,
            )
        player.deck.cards_in_river[move.river_slot_destination].append(move.card)

    # ------------------------------------------------------------------
    # Source effects
    # ------------------------------------------------------------------

    def _apply_source_effects(self, move: Move, player: PlayerState) -> None:
        """Remove the card from the source pile."""
        if move.source_pile == "NertzPile":
            self._remove_from_nertz(move, player)
        elif move.source_pile == "DeckPile":
            self._remove_from_stream(move, player)
        elif move.source_pile == "RiverPile":
            self._remove_from_river(move, player)

    def _remove_from_nertz(self, move: Move, player: PlayerState) -> None:
        """Pop the top card from the nertz pile, verifying it matches."""
        pile = player.deck.cards_in_nertz
        if pile and pile[-1].equals(move.card):
            pile.pop()
        else:
            raise CardMismatchError(
                expected=move.card,
                actual=pile[-1] if pile else None,
                pile_name="NertzPile",
                player_index=move.player_index,
            )

    def _remove_from_stream(self, move: Move, player: PlayerState) -> None:
        """Pop the top card from the deck stream, verifying it matches."""
        pile = player.deck.cards_in_stream
        if pile and pile[-1].equals(move.card):
            pile.pop()
        else:
            raise CardMismatchError(
                expected=move.card,
                actual=pile[-1] if pile else None,
                pile_name="DeckPile (stream)",
                player_index=move.player_index,
            )

    def _remove_from_river(self, move: Move, player: PlayerState) -> None:
        """Remove a card from a river slot.

        For river-to-river moves the *bottom* card of the source slot is
        verified (the whole pile is being moved).  For all other moves the
        *top* card is verified and popped.
        """
        self.logger.log_debug(
            f"Removing card {move.card} from RiverPile "
            f"(player={move.player_index}, slot={move.river_slot_source})"
        )
        if move.river_slot_source is None:
            raise MoveValidationError(
                "River slot source index must be specified for RiverPile moves.",
                player_index=move.player_index,
            )
        slot = player.deck.cards_in_river[move.river_slot_source]

        if move.destination_pile == "RiverPile":
            # Whole-pile move: verify the bottom card matches
            if slot and slot[0].equals(move.card):
                slot.pop(0)
            else:
                self.logger.log_debug(f"RiverPile slot cards: {slot}")
                raise CardMismatchError(
                    expected=move.card,
                    actual=slot[0] if slot else None,
                    pile_name=f"RiverPile (slot {move.river_slot_source}, bottom)",
                    player_index=move.player_index,
                )
        else:
            # Single-card move: verify the top card matches
            if slot and slot[-1].equals(move.card):
                slot.pop()
            else:
                self.logger.log_debug(f"RiverPile slot cards: {slot}")
                raise CardMismatchError(
                    expected=move.card,
                    actual=slot[-1] if slot else None,
                    pile_name=f"RiverPile (slot {move.river_slot_source}, top)",
                    player_index=move.player_index,
                )
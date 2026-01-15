from typing import List, Literal, Optional, TypeAlias
from dataclasses import dataclass
from enum import Enum

from nertz.models.game import GameState
from nertz.models.cards import PlayingCard, RANKS
from nertz.engine.layout import Point
from nertz.utils.constants import FoundationIdentifier

@dataclass
class GameResult:
    """Results from a completed game"""
    winner: int
    turns_played: int
    final_scores: List[int]
    foundations_created: int
    game_duration_seconds: float

class MoveType(Enum):
    """All the possible move types in Nertz."""
    NERTZ_TO_FOUNDATION = "NertzToFoundation"
    RIVER_TO_FOUNDATION = "RiverToFoundation"
    DECK_TO_FOUNDATION  = "DeckToFoundation"
    DECK_TO_RIVER      = "DeckToRiver"
    NERTZ_TO_RIVER     = "NertzToRiver"
    RIVER_TO_RIVER     = "RiverToRiver"

# Base priority weights per move type
MOVE_TYPE_WEIGHTS: dict[MoveType, float] = {
    MoveType.NERTZ_TO_FOUNDATION: 1.0,
    MoveType.NERTZ_TO_RIVER:      0.9,
    MoveType.RIVER_TO_FOUNDATION: 0.5,
    MoveType.DECK_TO_FOUNDATION:  0.4,
    MoveType.DECK_TO_RIVER:       0.3,
    MoveType.RIVER_TO_RIVER:      0.3,
}

LocationType: TypeAlias = Literal[
    "NertzPile",
    "RiverPile",
    "DeckPile",
    "FoundationPile",
]

@dataclass
class Move:
    """Represents a player's move"""
    player_index: int
    game_state: GameState
    source_pile: LocationType
    destination_pile: LocationType
    card: PlayingCard
    distance: float
    move_type: MoveType
    _priority: float = 0.0
    foundation_identifier: Optional[str] = None
    """The foundation identifier the card is placed into, if applicable"""
    river_slot_source: Optional[int] = None
    """The river slot index the card is taken from, if applicable"""
    river_slot_destination: Optional[int] = None
    """The river slot index the card is placed into, if applicable"""

    def __post_init__(self):
        if self.destination_pile == "FoundationPile" and not self.foundation_identifier:
            raise ValueError("foundation_identifier must be provided for FoundationPile moves")
        if self.source_pile == "RiverPile" and self.river_slot_source is None:
            raise ValueError("river_slot_source must be provided for RiverPile source moves")
        if self.destination_pile == "RiverPile" and self.river_slot_destination is None:
            raise ValueError("river_slot_destination must be provided for RiverPile destination moves")

        # Base priority weight for this move type
        base_weight = MOVE_TYPE_WEIGHTS.get(self.move_type, 0.5)

        # Distance penalty: closer moves get bonus, farther moves get penalty
        # Distance ranges from 0.0 (same location) to 1.0 (maximum distance)
        distance_factor = 1.0 - (self.distance * 0.3)  # 30% max penalty for distance
        
        # Strategic bonuses
        strategic_bonus = self._calculate_strategic_bonus()
        
        # Calculate final priority
        self.priority = base_weight * distance_factor + strategic_bonus
    
    def _calculate_strategic_bonus(self) -> float:
        """Calculate additional strategic bonuses for specific situations"""
        bonus = 0.0
        
        # Bonus for nertz moves (reduces main objective pile)
        if self.source_pile == "NertzPile":
            # Extra bonus if moving to a foundation
            if self.destination_pile == "FoundationPile":
                # Check if this foundation is the only one of its suit
                duplicate_foundation = False
                for foundation in self.game_state.foundations.values():
                    if (foundation.suit == self.card.suit and
                        foundation.identifier != self.foundation_identifier):
                        duplicate_foundation = True
                        break
                if not duplicate_foundation:
                    # Nertz cards that are higher rank get more bonus because
                    # they are harder to play later since the foundation is the
                    # only one of its suit.
                    weight = (RANKS.index(self.card.rank) + 1) / 13.0
                    bonus += weight * 20.0

        # Need to add more nuances later
        
        return bonus

"""Engine TODOs:"""
# TODO: Implement timeouts and asynchronous move calculations for players
# TODO: Implement more sophisticated conflict resolution strategies
# TODO: Implement scoring and end-game conditions
# TODO: Route print calls to a separate logger layer
# TODO: Add unit tests for move priority calculations and conflict resolution

class NertzEngine:
    def __init__(self, player_count: int = 2):
        self.player_count = player_count
        self.game_state : GameState = GameState(player_count=player_count)
        self.turn_counter = 0

    def _distance_player_to_river(self, player_index: int) -> float:
        """Approximate distance from player to their river area."""
        table = self.game_state.table
        player_pos = Point(*table.get_player_position(player_index))
        # If river is conceptually at the player's position, distance can just be 0.0;
        # keep this method so you can change the model later without touching all callers.
        return table.distance_between(player_pos, player_pos)
        
    def start_new_game(self) -> None:
        """Initialize a new game"""
        self.turn_counter = 0
    
    """Engine operates on fixed time intervals:
    1. Each player calculates legal moves (with timeout)
    2. Best move selected via heuristic
    3. Conflicting moves resolved by priority + randomization
    4. Moves executed based on priority comparison"""

    def play_turn(self) -> None:
        """Simulate a single turn of the game"""
        if not self.game_state:
            raise ValueError("Game has not been started.")

        if self.is_game_over():
            print("Game over. Cannot play further turns.")
            return

        print(f"--- Turn {self.turn_counter + 1} ---")
        
        # Placeholder logic for a turn
        self.turn_counter += 1

        chosen_moves_list : List[Move] = []
        
        for player in self.game_state.players:
            table = self.game_state.table
            player_pos = table.get_player_position(player.player_index)
            calculated_moves = self.calculate_legal_moves(player.player_index)
            print("-------------")
            print(f"Player {player.player_index} at position {player_pos} has {len(calculated_moves)} legal moves.")
            # Print player's river and stream cards
            print("[RIVER]:")
            for i, river_pile in enumerate(player.deck.cards_in_river):
                if river_pile:
                    top_card = river_pile[-1]
                    print(f"  SLOT {i}: Top card is {top_card}")
                else:
                    print(f"  River Pile {i}: Empty")
            print("Stream Cards:")
            for i, stream_card in enumerate(player.deck.cards_in_stream):
                if stream_card:
                    print(f"  {stream_card}")
                else:
                    print(f"  Stream Card {i}: Empty")

            print("Moves:")
            highest_total = -1.0
            chosen_move = None
            for move in calculated_moves:
                print(f"  Move {move.card} from {move.source_pile} to {move.destination_pile} with priority {move.priority:.2f} and distance {move.distance:.2f}")
                combined_score = move.priority + move.distance
                if combined_score > highest_total:
                    highest_total = combined_score
                    chosen_move = move

            if chosen_move:
                chosen_moves_list.append(chosen_move)
                print(f"Chosen Move: {chosen_move.card} from {chosen_move.source_pile} to {chosen_move.destination_pile} with priority {chosen_move.priority:.2f} and distance {chosen_move.distance:.2f}")
        

        print("Resolving conflicts and executing moves...")

        """First, identify which moves can be executed without conflict.
        Conflicts only arise when two moves have the same foundation destination.
        We will group these by their destination identifier then use further 
        algorithmic heuristics to resolve."""
    
        conflict_map : dict[FoundationIdentifier, List[Move]] = {}

        for move in chosen_moves_list:
            if move.destination_pile != "FoundationPile":
                # No conflict possible
                self.execute_move(move)
                continue
            
            if move.card.rank == "A":
                # Aces always create new foundations, no conflict
                self.execute_move(move)
                continue

            dest_id = move.foundation_identifier
            if dest_id not in conflict_map:
                conflict_map[dest_id] = []
            conflict_map[dest_id].append(move)

        for foundation_id, foundation_moves in conflict_map.items():
            if len(foundation_moves) == 1:
                # No conflict
                self.execute_move(foundation_moves[0])
            else:
                # Resolve conflict by priority
                # Custom sort: priority desc, distance asc, player_index asc
                foundation_moves.sort(
                    key=lambda m: (-m.priority, m.distance, m.player_index)
                )
                best_move = foundation_moves[0]
                self.execute_move(best_move)
                print(f"Conflict on foundation {foundation_id}. Executed move by Player {best_move.player_index} with priority {best_move.priority:.2f}. Other moves discarded.")
            
    def execute_move(self, move: Move) -> None:
        print(f"Executing move: Player {move.player_index} moves {move.card} from {move.source_pile} to {move.destination_pile}")
        player = self.game_state.players[move.player_index]

        self._apply_destination_effects(move, player)
        self._apply_source_effects(move, player)

        print(f"Move executed successfully.")

    def _apply_destination_effects(self, move: Move, player) -> None:
        """Place the card in the destination pile."""
        if move.destination_pile == "FoundationPile":
            if move.card.rank == "A":
                # Create new foundation
                self.game_state.create_foundation(move.card, move.player_index)
            else:
                foundation_id = move.foundation_identifier
                foundation = self.game_state.foundations.get(foundation_id)
                if foundation:
                    foundation.add_card(move.card)
                else:
                    raise ValueError(f"Foundation {foundation_id} does not exist.")
        elif move.destination_pile == "RiverPile":
            if move.river_slot_destination is None:
                raise ValueError("River slot destination index must be specified for RiverPile moves.")
            player.deck.cards_in_river[move.river_slot_destination].append(move.card)
        # DeckPile and NertzPile are never a destination in the current ruleset

    def _apply_source_effects(self, move: Move, player) -> None:
        """Remove the card from the source pile."""
        if move.source_pile == "NertzPile":
            if player.deck.cards_in_nertz and player.deck.cards_in_nertz[-1] == move.card:
                player.deck.cards_in_nertz.pop()
            else:
                raise ValueError("Top Nertz card does not match the move card.")
            
        elif move.source_pile == "DeckPile":
            if player.deck.cards_in_stream and player.deck.cards_in_stream[-1] == move.card:
                player.deck.cards_in_stream.pop()
            else:
                raise ValueError("Top Deck stream card does not match the move card.")
            
        elif move.source_pile == "RiverPile":
            print(f"Removing card {move.card} from RiverPile")
            if move.river_slot_source is None:
                raise ValueError("River slot source index must be specified for RiverPile moves.")
            slot = player.deck.cards_in_river[move.river_slot_source]
            if slot and slot[-1] == move.card:
                slot.pop()
            else:
                raise ValueError("Top River card does not match the move card.")
                

    def generate_river_move(self, player_index: int, card: PlayingCard, source_pile: LocationType) -> Optional[Move]:
        """Generate a move to river if possible"""
        if source_pile == "RiverPile":
            raise ValueError("Do not use this method for river to river moves.")
        
        if not self.game_state:
            return None
        
        player = self.game_state.players[player_index]
        distance = self._distance_player_to_river(player_index)
        
        def _build_river_move(river_slot_index: int) -> Move:
            return Move(
                player_index=player_index,
                game_state=self.game_state,
                source_pile=source_pile,
                destination_pile="RiverPile",
                river_slot_destination=river_slot_index,
                move_type=MoveType.DECK_TO_RIVER if source_pile == "DeckPile" else MoveType.NERTZ_TO_RIVER,
                card=card,
                distance=distance
            )

        for i in range(4):
            # Check for empty list 
            if not player.deck.cards_in_river[i]:
                move = _build_river_move(i)
                return move
            elif self._is_valid_solitaire_move(card, player.deck.cards_in_river[i][-1]):
                move = _build_river_move(i)
                return move
        
        return None

    def generate_foundation_move(self, player_index: int, card: PlayingCard, source_pile: LocationType, river_slot_source_index: Optional[int] = None) -> Optional[Move]:
        """Generate a move to foundation if possible"""
        if not self.game_state:
            return None
        
        table = self.game_state.table
        player_pos = Point(*table.get_player_position(player_index))
        
        move_type = None
        if source_pile == "NertzPile":
            move_type = MoveType.NERTZ_TO_FOUNDATION
        elif source_pile == "RiverPile":
            move_type = MoveType.RIVER_TO_FOUNDATION
        elif source_pile == "DeckPile":
            move_type = MoveType.DECK_TO_FOUNDATION
        else:
            raise ValueError(f"Unsupported source_pile for foundation move: {source_pile}")

        def _build_foundation_move(foundation_id: str, foundation_pos: Point) -> Move:
            distance = table.distance_between(player_pos, foundation_pos)
            return Move(
                player_index=player_index,
                game_state=self.game_state,
                source_pile=source_pile,
                river_slot_source=river_slot_source_index,
                destination_pile="FoundationPile",
                foundation_identifier=foundation_id,
                move_type=move_type,
                card=card,
                distance=distance
            )

        if card.rank == "A":
            # Can always start a new foundation with an Ace
            foundation_id = f"foundation_{player_index}_{card.suit}"
            foundation_position = self.game_state.table.place_foundation(foundation_id)
            return _build_foundation_move(foundation_id, foundation_position)
        
        for foundation in self.game_state.foundations.values():
            if (card.suit == foundation.suit) and (card.rank == self._next_rank(foundation.top().rank)):
                foundation_pos = Point(*table.get_foundation_position(foundation.identifier))
                return _build_foundation_move(foundation.identifier, foundation_pos)
        
        return None

    def calculate_legal_moves(self, player_index: int) -> List[Move]:
        """Calculate legal moves for a player"""
        if not self.game_state:
            return []
        
        legal_moves : List[Move] = []
        
        self._add_nertz_moves(player_index, legal_moves)
        self._add_river_to_foundation_moves(player_index, legal_moves)
        self._add_river_to_river_moves(player_index, legal_moves)
        self._add_deck_moves(player_index, legal_moves)

        return legal_moves

    def _add_nertz_moves(self, player_index: int, legal_moves: List[Move]) -> None:
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

    def _add_river_to_foundation_moves(self, player_index: int, legal_moves: List[Move]) -> None:
        player = self.game_state.players[player_index]
        for i in range(4):
            current_river_pile = player.deck.cards_in_river[i]
            if not current_river_pile:
                continue
            river_card = current_river_pile[-1]  # Top card of the pile
            move = self.generate_foundation_move(player_index, river_card, "RiverPile", river_slot_source_index=i)
            if move:
                legal_moves.append(move)

    def _add_river_to_river_moves(self, player_index: int, legal_moves: List[Move]) -> None:
        player = self.game_state.players[player_index]
        table = self.game_state.table

        for i in range(4):
            current_river_pile = player.deck.cards_in_river[i]
            if not current_river_pile:
                continue
            source_card = current_river_pile[0]  # Bottom card of the pile
            for j in range(4): 
                if i == j:
                    continue
                dest_river_pile = player.deck.cards_in_river[j]
                if not dest_river_pile:
                    continue
                dest_card = dest_river_pile[-1]  # Top card of the destination pile
                if self._is_valid_solitaire_move(source_card, dest_card):
                    distance = self._distance_player_to_river(player_index)

                    print(f"Legal RiverToRiver move found: {source_card} from slot {i} to slot {j}")

                    move = Move(
                        player_index=player_index,
                        game_state=self.game_state,
                        source_pile="RiverPile",
                        destination_pile="RiverPile",
                        river_slot_source=i,
                        river_slot_destination=j,
                        move_type=MoveType.RIVER_TO_RIVER,
                        card=source_card,
                        distance=distance
                    )
                    legal_moves.append(move)

    def _add_deck_moves(self, player_index: int, legal_moves: List[Move]) -> None:
        player = self.game_state.players[player_index]
        if not player.deck.cards_in_deck:
            return

        # Check the top 3 cards in the stream
        top_deck_cards = player.deck.cards_in_stream[-3:]
        for deck_card in top_deck_cards:
            if deck_card is None:
                continue
            move = self.generate_river_move(player_index, deck_card, "DeckPile")
            if move:
                legal_moves.append(move)
            else:
                move = self.generate_foundation_move(player_index, deck_card, "DeckPile")
                if move:
                    legal_moves.append(move)

    def _next_rank(self, rank: str) -> str:
        """Get the next rank in sequence"""
        if rank not in RANKS:
            raise ValueError(f"Invalid rank: {rank}")
        
        index = RANKS.index(rank)
        if index + 1 < len(RANKS):
            return RANKS[index + 1]
        else:
            return ""  # No next rank after King
        
    def _is_valid_solitaire_move(self,  source_card: PlayingCard, dest_card: PlayingCard) -> bool:
        """Check if source_card can be placed on dest_card in solitaire rules"""
        if source_card.suit in ["hearts", "diamonds"] and dest_card.suit in ["spades", "clubs"]:
            # source is red, dest is black
            return self._next_rank(source_card.rank) == dest_card.rank
        elif source_card.suit in ["spades", "clubs"] and dest_card.suit in ["hearts", "diamonds"]:
            # source is black, dest is red
            return self._next_rank(source_card.rank) == dest_card.rank
        
        return False

    def is_game_over(self) -> bool:
        """Check if the game has ended"""
        if not self.game_state:
            return False
        
        # Placeholder logic for game over condition
        for player in self.game_state.players:
            if len(player.deck.cards_in_nertz) == 0:
                return True
        
        return False
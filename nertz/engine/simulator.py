from typing import List, Literal, Optional, TypeAlias
from dataclasses import dataclass
from nertz.models.game import GameState
from nertz.models.cards import PlayingCard, SUIT, SUITS, RANK, RANKS
from nertz.engine.layout import Table, Point

@dataclass
class GameResult:
    """Results from a completed game"""
    winner: int
    turns_played: int
    final_scores: List[int]
    foundations_created: int
    game_duration_seconds: float

"""All the possible move types in Nertz"""
MOVE_NERTZ_TO_FOUNDATION = "NertzToFoundation"
MOVE_RIVER_TO_FOUNDATION = "RiverToFoundation"
MOVE_DECK_TO_RIVER = "DeckToRiver"
MOVE_NERTZ_TO_RIVER = "NertzToRiver"
MOVE_RIVER_TO_RIVER = "RiverToRiver"

MoveType : TypeAlias = Literal[
    "NertzToFoundation",
    "RiverToFoundation",
    "DeckToRiver",
    "NertzToRiver",
    "RiverToRiver"
]

LocationType : TypeAlias = Literal[
    "NertzPile",
    "RiverPile",
    "DeckPile",
    "FoundationPile"
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
    _priority: float = 0.0
    destination_identifier: Optional[str] = None # For foundations

    def __post_init__(self):
        # Base priority weights for move types
        move_type_weights = {
            ("NertzPile", "FoundationPile"): 1.0,    
            ("NertzPile", "RiverPile"): 0.9,         
            ("RiverPile", "FoundationPile"): 0.5,      
            ("DeckPile", "FoundationPile"): 0.5,       
            ("DeckPile", "RiverPile"): 0.3,             
            ("RiverPile", "RiverPile"): 0.3,           
        }
        
        # Get base weight for this move type
        move_key = (self.source_pile, self.destination_pile)
        base_weight = move_type_weights.get(move_key, 0.5)  # Default weight if not found
        
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
                        foundation.identifier != self.destination_identifier):
                        duplicate_foundation = True
                        break
                if not duplicate_foundation:
                    # Nertz cards that are higher rank get more bonus because
                    # they are harder to play later since the foundation is the
                    # only one of its suit.
                    weight = RANKS.index(self.card.rank) + 1 / 13.0
                    bonus += weight * 20.0
    
        
        return bonus

class NertzEngine:
    def __init__(self, player_count: int = 2):
        self.player_count = player_count
        self.game_state : GameState = GameState(player_count=player_count)
        self.turn_counter = 0
        
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

        chose_move_list = []
        
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
                chose_move_list.append(chosen_move)
                print(f"Chosen Move: {chosen_move.card} from {chosen_move.source_pile} to {chosen_move.destination_pile} with priority {chosen_move.priority:.2f} and distance {chosen_move.distance:.2f}")
        
        foundation_moves = [move for move in chose_move_list if move.destination_pile == "FoundationPile"]
        for move in foundation_moves:
            self.execute_move(move)
            print(f"Executed Move: {move.card} from {move.source_pile} to {move.destination_pile}")
            
    def execute_move(self, move: Move) -> None:
        # Start here next time you start coding
        # we need to implement the actual move execution logic
        pass

    def generate_river_move(self, player_index: int, card: PlayingCard, source_pile: LocationType) -> Optional[Move]:
        """Generate a move to river if possible"""
        if not self.game_state:
            return None
        
        player = self.game_state.players[player_index]
        table = self.game_state.table
        
        for i in range(4):
            # Check for empty list 
            if not player.deck.cards_in_river[i]:
                distance = table.distance_between(
                    Point(*table.get_player_position(player_index)),
                    Point(*table.get_player_position(player_index))  # Assuming river is near player
                )

                move = Move(
                    player_index=player_index,
                    game_state=self.game_state,
                    source_pile=source_pile,
                    destination_pile="RiverPile",
                    card=card,
                    distance=distance
                )
                return move
            elif card.rank == self._is_valid_solitaire_move(card, player.deck.cards_in_river[i][-1]):
                distance = table.distance_between(
                    Point(*table.get_player_position(player_index)),
                    Point(*table.get_player_position(player_index))  # Assuming river is near player
                )

                move = Move(
                    player_index=player_index,
                    game_state=self.game_state,
                    source_pile=source_pile,
                    destination_pile="RiverPile",
                    card=card,
                    distance=distance
                )
                return move
        
        return None

    def generate_foundation_move(self, player_index: int, card: PlayingCard, source_pile: LocationType) -> Optional[Move]:
        """Generate a move to foundation if possible"""
        if not self.game_state:
            return None
        
        table = self.game_state.table

        if card.rank == "A":
            # Can always start a new foundation with an Ace
            foundation_position = self.game_state.table.place_foundation(f"foundation_{player_index}_{card.suit}")

            distance = table.distance_between(
                Point(*table.get_player_position(player_index)),
                foundation_position
            )

            move = Move(
                player_index=player_index,
                game_state=self.game_state,
                source_pile=source_pile,
                destination_pile="FoundationPile",
                card=card,
                distance=distance
            )
            return move
        
        for foundation in self.game_state.foundations.values():
            if (card.suit == foundation.suit) and (card.rank == self._next_rank(foundation.top().rank)):
                distance = table.distance_between(
                    Point(*table.get_player_position(player_index)),
                    Point(*table.get_foundation_position(foundation.identifier))
                )

                move = Move(
                    player_index=player_index,
                    game_state=self.game_state,
                    source_pile=source_pile,
                    destination_pile="FoundationPile",
                    card=card,
                    distance=distance
                )
                return move
        
        return None

    def calculate_legal_moves(self, player_index: int) -> List[Move]:
        """Calculate legal moves for a player"""
        if not self.game_state:
            return []
        
        player = self.game_state.players[player_index]
        table = self.game_state.table
        legal_moves : List[Move] = []
        
        """Check NertzToFoundation and NertzToRiver moves"""
        if player.deck.cards_in_nertz:
            nertz_card = player.deck.top_nertz_card()
            if nertz_card:
                move = self.generate_foundation_move(player_index, nertz_card, "NertzPile")
                if move:
                    legal_moves.append(move)

                else:
                    move = self.generate_river_move(player_index, nertz_card, "NertzPile")
                    if move:
                        legal_moves.append(move)

        """Check RiverToFoundation moves"""
        for river_slot in player.deck.cards_in_river:
            if not river_slot:
                continue
            move = self.generate_foundation_move(player_index, river_slot[-1], "RiverPile")
            if move:
                legal_moves.append(move)
        
        """
        Check RiverToRiver solitaire moves. Legal if destination's top card
        is one rank higher and opposite color than source's bottom card.
        Only checking full pile moves to free up river slots.
        """
        for i in range(4):
            current_river_pile = player.deck.cards_in_river[i]
            if not current_river_pile:
                continue
            source_card = current_river_pile[0]  # Bottom card of the pile
            for j in range(4): 
                if i == j:
                    # Skip same pile
                    continue
                dest_river_pile = player.deck.cards_in_river[j]
                if not dest_river_pile:
                    continue
                dest_card = dest_river_pile[-1]  # Top card of the destination pile
                if self._is_valid_solitaire_move(source_card, dest_card):
                    distance = table.distance_between(
                        Point(*table.get_player_position(player_index)),
                        Point(*table.get_player_position(player_index))  # Assuming river is near player
                    )

                    move = Move(
                        player_index=player_index,
                        game_state=self.game_state,
                        source_pile="RiverPile",
                        destination_pile="RiverPile",
                        card=source_card,
                        distance=distance
                    )
                    legal_moves.append(move)

        
        """Check DeckToRiver and DeckToFoundation moves"""
        if player.deck.cards_in_deck:
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

        
        return legal_moves

    def _next_rank(self, rank: str) -> str:
        """Get the next rank in sequence"""
        ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        if rank not in ranks:
            raise ValueError(f"Invalid rank: {rank}")
        
        index = ranks.index(rank)
        if index + 1 < len(ranks):
            return ranks[index + 1]
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

    def is_game_over(self) -> bool:
        """Check if the game has ended"""
        if not self.game_state:
            return False
        
        # Placeholder logic for game over condition
        for player in self.game_state.players:
            if len(player.deck.cards_in_nertz) == 0:
                return True
        
        return False
"""Game state models."""
from typing import List, TypeAlias
from nertz.core.deck import DeckManager
from nertz.engine.layout import Table
from nertz.core.foundation import Foundation
from nertz.utils.constants import PlayerIndex, FoundationKey



"""Represents a player in the game, managing their score and deck."""
class PlayerState:
    def __init__(self, player_index: PlayerIndex):
        self.player_index: PlayerIndex = player_index
        self.score: int = 0
        self.deck: DeckManager = DeckManager(player_index=player_index).deal_starting_hand()
        
"""The GameState class will manage the overall state of the game,
including player piles, foundations, and the table layout. I recognize
that nesting a table within the game state is not the cleanest design, but
it simplifies access to layout information for now."""
class GameState:

    def __init__(self, player_count: int):
        self.player_count = player_count

        self.players = []
        for i in range(player_count):
            player = PlayerState(player_index=i)
            self.players.append(player)

        self.foundations : dict[FoundationKey, Foundation] = {}
        """Keys are represented as: foundation_[PINDEX]_[SUIT]"""
        self.table : Table = Table(player_count)


    def validate_player_piles(self) -> bool:
        raise NotImplementedError("Use validators.validate_player_piles instead")
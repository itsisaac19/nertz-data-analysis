from nertz.models.game import GameState
from nertz.models.cards import PlayingCard

def validate_player_piles(game_state: GameState) -> bool:
    # ...existing logic moved from GameState.validate_player_piles...
    # but fix `player.deck[pile]` usage:
    for player in game_state.players:
        # ...existing code...
        for pile_name in ["cards_in_nertz", "cards_in_river", "cards_in_deck"]:
            pile = getattr(player.deck, pile_name)
            # handle nested river structure if needed, etc.
    # ...existing code...

from nertz.models.game import GameState
from nertz.utils.logger import Logger

INITIAL_NERTZ_COUNT = 13

def process_game_scores(game_state: GameState):
    """
    Player score is calculated as following:
    N = # of Nertz cards remaining (unplayed)
    L = # of Lake cards played
    Score = (N * -2) + L

    Each Nertz card left unplayed is -2 points.
    Each Lake card played is +1 point.
    """
    logger = Logger()
    logger.log("Game scores processed:")

    for player in game_state.players:
        # Remaining Nertz cards are just the current length of the pile
        nertz_remaining = len(player.deck.cards_in_nertz)

        # Lake cards: currently nothing moves into cards_in_lake,
        # so this will stay 0 until you implement that logic.
        lake_played = len(player.deck.cards_in_lake)

        score = (nertz_remaining * -2) + lake_played

        logger.log(
            f"Player {player.player_index}: "
            f"Nertz remaining={nertz_remaining}, Lake played={lake_played}, Score={score}"
        )

        player.score += score
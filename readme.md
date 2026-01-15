# Nertz Data Analysis & Simulation

This is a simulation engine for the card game **Nertz**, built as a side project to explore spatial layout, move generation, and automated gameplay.

The emphasis is on modeling the underlying system rather than making something playable: explicit game state, table geometry, and logic for choosing moves when multiple actions are possible at once.


## Structure

- `main.py`  
  Creates a `NertzEngine` and runs a short simulation.

- `nertz/models/`  
  - `cards.py` – Card types and constants.  
  - `game.py` – `PlayerState` and `GameState` (players, foundations, table layout).

- `nertz/core/`  
  - `deck.py` – `DeckManager` for Nertz, river, stream, deck, and lake piles.  
  - `foundation.py` – `Foundation` piles (ace‑up by suit).

- `nertz/engine/`  
  - `simulator.py` – `NertzEngine`, `Move`, `GameResult`; move generation, heuristics, and turn loop.  
  - `layout.py` – `Table` and `Point` for player/foundation positions and distances.  
  - `layout_visualization.py` – Matplotlib plot of layout.  
  - `validators.py` – Planned `GameState` validation helpers.

- `nertz/utils/`  
  - `constants.py` – Shared aliases like `PlayerIndex` and `FoundationKey`.

## Key Concepts

- **Spatial Layout**  
  Players are positioned deterministically around the perimeter of a normalized 2D unit square; foundations are clustered near the center with jitter and minimum spacing. Distances between positions are used to influence move priorities.

- **Move Heuristics**  
  Moves are evaluated based on:
  - Type (e.g., Nertz → Foundation, Deck → River).
  - Euclidean distance between source and destination.
  - Strategic bonuses, especially for reducing the Nertz pile and playing higher‑rank cards to unique foundations.

- **Foundations & Piles**  
Each player manages:
  - A Nertz pile (primary objective to empty).
  - River piles (solitaire‑style tableau).
  - A deck and stream (flipped in threes).
  - A lake pile for cards already played to foundations.

  
## Rules
Rules are based on [these standards](https://bicyclecards.com/how-to-play/nerts) by Bicycle Cards.
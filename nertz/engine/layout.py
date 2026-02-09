"""In an attempt to model realistic spatial interactions between players,
we will define a layout based on Euclidean distance between floating points
in a normalized space, where x and y are defined as the points in [0.0, 1.0].
We can also describe this space as the unit square in the first (I) quadrant.
Each CPU has a position on or near the perimeter of the unit square. Each 
foundation slot has a position near the center, diffused or jittered randomly.
Player positions will be deterministic to simplify implementation.
Reference values for a unit square with players on a perimeter circle 
radius ~0.48 and foundations in a center cluster radius ~0.12"""

import math, random
import matplotlib.pyplot as plt
from typing import TypeAlias, Union

from nertz.engine.constants import PlayerIndex
from nertz.utils.logger import Logger

# Point between 0.0 and 1.0
PointCoordinate : TypeAlias = float

class Point:
    """A point in 2D space with x and y coordinates between 0.0 and 1.0"""
    def __init__(self, x: PointCoordinate, y: PointCoordinate):
        self.x = x
        self.y = y

# Definition for a set of positions given an identifier
PositionSet : TypeAlias = dict[PlayerIndex, tuple[float, float]]

"""The Table class will manage player and foundation positions. It will NOT include
data about cards or piles, only spatial layout information. Once a position is selected,
its identifier can be used as a key to retrieve pile information from the GameState class."""
class Table:
    def __init__(self, player_count: int):
        self.player_count = player_count
        self.player_positions : PositionSet = {}
        self.foundation_positions : PositionSet = {}
        self._initialize_positions()
        self.logger = Logger()

    def distance_between(self, x1: Point, x2: Point) -> float:
        return math.sqrt((x1.x - x2.x) ** 2 + (x1.y - x2.y) ** 2)

    def _initialize_positions(self) -> None:
        angle_increment = 2 * math.pi / self.player_count
        radius = 0.48  # Radius for player positions

        for i in range(self.player_count):
            angle = i * angle_increment
            x = 0.5 + radius * math.cos(angle)
            y = 0.5 + radius * math.sin(angle)
            self.player_positions[i] = (x, y)

    def place_foundation(self, foundation_identifier: str) -> Point:
        """Places a foundation near the center with some random jitter,
        and returns the position as a Point."""
        # Place foundation near center with some random jitter
        jitter_x = random.uniform(-0.05, 0.05)
        jitter_y = random.uniform(-0.05, 0.05)
        x = 0.5 + jitter_x
        y = 0.5 + jitter_y

        # Use retry sampling to ensure foundations do not overlap too closely
        min_distance = 0.1  # Minimum distance between foundations
        max_retries = 100
        
        for attempt in range(max_retries):  # Retry up to 100 times
            # Expand search radius with each attempt
            base_radius = 0.05 + (attempt * 0.01)  # Start at 0.05, grow to 0.14
            
            jitter_x = random.uniform(-base_radius, base_radius)
            jitter_y = random.uniform(-base_radius, base_radius)
            x = 0.5 + jitter_x
            y = 0.5 + jitter_y
            
            # Ensure we stay within bounds
            x = max(0.0, min(1.0, x))
            y = max(0.0, min(1.0, y))

            too_close = False

            for _, (ox, oy) in self.foundation_positions.items():
                dist = math.sqrt((x - ox) ** 2 + (y - oy) ** 2)
                if dist < min_distance:
                    too_close = True
                    break

            if not too_close:
                self.logger.log_debug(f"Placed {foundation_identifier} after {attempt} tries")
                self.foundation_positions[foundation_identifier] = (x, y)
                return Point(x, y)

        self.logger.log(f"Warning: Could not place {foundation_identifier} without overlap after {max_retries} tries.")
        # Place anyway at last attempted position
        self.foundation_positions[foundation_identifier] = (x, y)
        return Point(x, y)

    def get_player_position(self, player_index: PlayerIndex) -> tuple[float, float]:
        float_positions = self.player_positions[player_index]
        rounded_positions = (round(float_positions[0], 4), round(float_positions[1], 4))
        return rounded_positions
    
    def get_foundation_position(self, foundation_identifier) -> tuple[float, float]:
        float_positions = self.foundation_positions[foundation_identifier]
        rounded_positions = (round(float_positions[0], 4), round(float_positions[1], 4))
        return rounded_positions



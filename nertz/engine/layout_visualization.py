import matplotlib.pyplot as plt
from .layout import Table

def visualize_layout(table: Table) -> None:
    # Create plot
    plt.figure(figsize=(6,6))
    
    # Plot player positions
    for player_index, (px, py) in table.player_positions.items():
        plt.plot(px, py, 'bo')  # Blue dot for player
        plt.text(px, py, f"P{player_index}", fontsize=12, ha='right')
    # Plot foundation positions
    for foundation_id, (fx, fy) in table.foundation_positions.items():
        plt.plot(fx, fy, 'ro')  # Red dot for foundation
        plt.text(fx, fy, f"{foundation_id}", fontsize=10, ha='left')
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    plt.title("Table Layout: Player and Foundation Positions")
    plt.xlabel("X Coordinate")
    plt.ylabel("Y Coordinate")
    plt.grid(True)
    plt.show()
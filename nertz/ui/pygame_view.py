import pygame
from pathlib import Path
from nertz.engine.simulator import NertzEngine

"""A simple Pygame-based view for visualizing the Nertz game state."""
class PygameNertzView:
    def __init__(self, engine: NertzEngine, width: int = 1200, height: int = 1000):
        pygame.init()
        self.engine = engine
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Nertz Simulation")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 18)

        """Image Cache and Loading"""
        self.card_w, self.card_h = 64, 96  # a bit bigger than before
        self.card_images: dict[str, pygame.Surface] = {}
        self.card_back = None
        self._load_card_images()


    def _load_card_images(self):
        """Load card images into a cache, scaled to card_w x card_h."""
        base = Path(__file__).resolve().parent.parent / "assets" / "cards"

        def load(name: str) -> pygame.Surface | None:
            path = base / name
            if not path.exists():
                return None
            img = pygame.image.load(str(path)).convert_alpha()
            return pygame.transform.smoothscale(img, (self.card_w, self.card_h))

        # Load a generic back
        self.card_back = load("back_light.png")

        """File format is [SUIT]_[RANK].png, e.g. clubs_7.png, hearts_A.png"""
        ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        suits = ["spades", "hearts", "diamonds", "clubs"]
        for r in ranks:
            for s in suits:
                key = f"{s}_{r}"
                img = load(f"{key}.png")
                if img:
                    self.card_images[key] = img
                else:
                    print(f"Warning: Missing card image for {key}")
    
    def get_image_key(self, card) -> str:
        """Get the image key for a given PlayingCard."""
        return f"{card.suit}_{card.rank}"

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # if window closed,
                    # stop running
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    # if spacebar pressed,
                    # advance one simulated turn
                    self.engine.play_turn()

            self.draw()
            pygame.display.flip()
            self.clock.tick(30)

        pygame.quit()

    def draw(self):
        """Draw the current game state using normalized table coordinates.

        The table/layout code gives positions in the unit square [0.0, 1.0]^2.
        We map those to pixel coordinates on the Pygame surface.
        """
        # Clear screen with a felt-like green background
        self.screen.fill((0, 100, 0))

        width, height = self.screen.get_size()

        # --- Add padding around the unit square ---
        # Fractions of the screen reserved as padding on each side
        pad_x = 0.15  # 10% left and right
        pad_y = 0.20  # 10% top and bottom

        usable_w = width * (1.0 - 2 * pad_x)
        usable_h = height * (1.0 - 2 * pad_y)

        # Helper to convert normalized (0..1, 0..1) to pixel coords with padding
        def to_screen(pos: tuple[float, float]) -> tuple[int, int]:
            nx, ny = pos
            sx = int(pad_x * width + nx * usable_w)
            sy = int(pad_y * height + ny * usable_h)
            return sx, sy
        
        table = self.engine.game_state.table

        # --- Draw players and their river piles ---
        for player in self.engine.game_state.players:
            px_norm, py_norm = table.get_player_position(player.player_index)
            px, py = to_screen((px_norm, py_norm))

            # Player marker
            pygame.draw.circle(self.screen, (255, 255, 0), (px, py), 12)
            label = self.font.render(str(player.player_index), True, (0, 0, 0))
            self.screen.blit(label, (px - 5, py - 8))

            # Use slightly larger cards now
            river_offset_y = 50
            river_spacing_x = self.card_w + 8
            card_w, card_h = self.card_w, self.card_h

            for i, pile in enumerate(player.deck.cards_in_river):
                card_x = px + (i - 2) * river_spacing_x
                card_y = py + river_offset_y
                rect = pygame.Rect(int(card_x), int(card_y), card_w, card_h)

                if pile:
                    top = pile[-1]
                    key = self.get_image_key(top)
                    img = self.card_images.get(key)

                    if img is not None:
                        # Center the card image in the rect
                        self.screen.blit(img, rect)
                    else:
                        # Fallback: plain rectangle with text
                        pygame.draw.rect(self.screen, (255, 255, 255), rect, border_radius=6)
                        pygame.draw.rect(self.screen, (0, 0, 0), rect, width=1, border_radius=6)
                        label_text = f"{top.rank}{top.suit[0].upper()}"
                        text = self.font.render(label_text, True, (0, 0, 0))
                        self.screen.blit(text, (rect.x + 4, rect.y + card_h // 2 - 8))
                else:
                    # Empty pile slot
                    if self.card_back:
                        self.screen.blit(self.card_back, rect)
                    else:
                        pygame.draw.rect(self.screen, (60, 60, 60), rect, border_radius=6)
                        pygame.draw.rect(self.screen, (0, 0, 0), rect, width=1, border_radius=6)

        # --- Foundations ---
        for foundation in self.engine.game_state.foundations.values():
            fx_norm, fy_norm = table.get_foundation_position(foundation.identifier)
            fx, fy = to_screen((fx_norm, fy_norm))
            card_w, card_h = self.card_w, self.card_h
            rect = pygame.Rect(int(fx - card_w / 2), int(fy - card_h / 2), card_w, card_h)

            top = foundation.top()
            if top:
                key = self.get_image_key(top)
                img = self.card_images.get(key)
                if img is not None:
                    self.screen.blit(img, rect)
                else:
                    pygame.draw.rect(self.screen, (230, 230, 230), rect, border_radius=6)
                    pygame.draw.rect(self.screen, (0, 0, 0), rect, width=1, border_radius=6)
                    label_text = f"{top.rank}{top.suit[0].upper()}"
                    text = self.font.render(label_text, True, (0, 0, 0))
                    self.screen.blit(text, (rect.x + 4, rect.y + card_h // 2 - 8))
            else:
                # Empty foundation slot
                pygame.draw.rect(self.screen, (200, 200, 200), rect, border_radius=6)
                pygame.draw.rect(self.screen, (0, 0, 0), rect, width=1, border_radius=6)
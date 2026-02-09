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
        self.font = pygame.font.Font("nertz/assets/fonts/IconaSansTRIAL-Medium.ttf", 18)

        """Image Cache and Loading"""
        self.card_w, self.card_h = 48, 72  # Standard card size
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

    # Helper to convert normalized (0..1, 0..1) to pixel coords with padding
    def convert_position_to_screen(self, pos: tuple[float, float]) -> tuple[int, int]:
        width, height = self.screen.get_size()

        pad_left: float = 0.10
        pad_right: float = 0.10
        pad_top: float = 0.05
        pad_bottom: float = 0.15

        usable_w = width * (1.0 - pad_left - pad_right)
        usable_h = height * (1.0 - pad_top - pad_bottom)

        nx, ny = pos
        sx = int(pad_left * width + nx * usable_w)
        sy = int(pad_top * height + ny * usable_h)
        return sx, sy

    def draw(self):
        """Draw the current game state using normalized table coordinates.

        The table/layout code gives positions in the unit square [0.0, 1.0]^2.
        We map those to pixel coordinates on the Pygame surface.
        """
        # Clear screen with a felt-like green background
        self.screen.fill((0, 100, 0))

        self.draw_player_markers()
        self.draw_rivers()
        self.draw_nertz_piles()
        self.draw_foundations()

    def draw_player_markers(self):
        """Draw player markers at their designated positions."""
        table = self.engine.game_state.table

        for player in self.engine.game_state.players:
            px_norm, py_norm = table.get_player_position(player.player_index)
            px, py = self.convert_position_to_screen((px_norm, py_norm))

            # Draw player name tag as Player {index}
            label_text = f"Player {player.player_index}"
            text = self.font.render(label_text, True, (255, 255, 255))
            self.screen.blit(text, (px - text.get_width() // 2, py - 20))


    def draw_rivers(self):
        """Draw the river piles for each player."""
        table = self.engine.game_state.table

        for player in self.engine.game_state.players:
            self._draw_player_river(player, table)

    def _draw_player_river(self, player, table) -> None:
        """Helper to draw a single player's river piles."""
        px_norm, py_norm = table.get_player_position(player.player_index)
        player_x, player_y = self.convert_position_to_screen((px_norm, py_norm))

        river_offset_y = 50
        river_spacing_x = self.card_w + 8
        card_w = self.card_w
        card_h = self.card_h

        for i, pile in enumerate(player.deck.cards_in_river):
            card_x = player_x + (i - 2) * river_spacing_x
            card_y = player_y + river_offset_y
            rect = pygame.Rect(int(card_x), int(card_y), card_w, card_h)
            self._draw_river_pile(pile, rect, card_h)

    def _draw_river_pile(self, pile, rect: pygame.Rect, card_h: int) -> None:
        if pile:
            self._draw_top_river_card(pile[-1], rect, card_h)
        else:
            self._draw_empty_river_slot(rect)

    def _draw_top_river_card(self, card, rect: pygame.Rect, card_h: int) -> None:
        key = self.get_image_key(card)
        img = self.card_images.get(key)

        if img is not None:
            self.screen.blit(img, rect)
            return

        pygame.draw.rect(self.screen, (255, 255, 255), rect, border_radius=6)
        pygame.draw.rect(self.screen, (0, 0, 0), rect, width=1, border_radius=6)
        label_text = f"{card.rank}{card.suit[0].upper()}"
        text = self.font.render(label_text, True, (0, 0, 0))
        self.screen.blit(text, (rect.x + 4, rect.y + card_h // 2 - 8))

    def _draw_empty_river_slot(self, rect: pygame.Rect) -> None:
        if self.card_back:
            self.screen.blit(self.card_back, rect)
            return

        pygame.draw.rect(self.screen, (60, 60, 60), rect, border_radius=6)
        pygame.draw.rect(self.screen, (0, 0, 0), rect, width=1, border_radius=6)

    
    def draw_nertz_piles(self):
        """The nertz pile should be drawn to the left of the river and down a bit."""
        table = self.engine.game_state.table

        # --- Draw Nertz piles ---
        for player in self.engine.game_state.players:
            px_norm, py_norm = table.get_player_position(player.player_index)
            px, py = self.convert_position_to_screen((px_norm, py_norm))

            nertz_offset_y = 70
            card_w, card_h = self.card_w, self.card_h

            rect = pygame.Rect(int(px - card_w * 3.5), int(py + nertz_offset_y), card_w, card_h)

            nertz_pile = player.deck.nertz_cards
            if nertz_pile:
                top = nertz_pile[-1]
                key = self.get_image_key(top)
                img = self.card_images.get(key)

                if img is not None:
                    self.screen.blit(img, rect)
                else:
                    pygame.draw.rect(self.screen, (255, 255, 255), rect, border_radius=6)
                    pygame.draw.rect(self.screen, (0, 0, 0), rect, width=1, border_radius=6)
                    label_text = f"{top.rank}{top.suit[0].upper()}"
                    text = self.font.render(label_text, True, (0, 0, 0))
                    self.screen.blit(text, (rect.x + 4, rect.y + card_h // 2 - 8))
            else:
                # Empty Nertz pile
                pygame.draw.rect(self.screen, (200, 200, 200), rect, border_radius=6)
                pygame.draw.rect(self.screen, (0, 0, 0), rect, width=1, border_radius=6)

    def draw_foundations(self):
        """Draw the foundation piles at their designated positions."""
        table = self.engine.game_state.table

        # --- Foundations ---
        for foundation in self.engine.game_state.foundations.values():
            fx_norm, fy_norm = table.get_foundation_position(foundation.identifier)
            fx, fy = self.convert_position_to_screen((fx_norm, fy_norm))
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
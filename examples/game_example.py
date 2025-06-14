"""
A complete, real-world example of the PureShell pattern using Pygame.
"""

# game_example.py
# pylint: disable=line-too-long,protected-access,no-member,invalid-name
import random
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, List

from pureshell import (
    Ruleset,
    StatefulEntity,
    ruleset_provider,
    shell_method,
    side_effect_method,
)

# It is the standard Python way to import types that may not be
# available at runtime without causing an ImportError.
if TYPE_CHECKING:
    from pygame.font import Font
    from pygame.surface import Surface
    from pygame.time import Clock

# This block handles the actual runtime import.
try:
    import pygame
except ImportError:
    print("Pygame is not installed. Please install it with 'pip install pygame'.")
    pygame = None  # Type: ignore[assignment]

# ==============================================================================
# --- 1. Game Configuration ---
# ==============================================================================

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PLAYER_SPEED = 5
ENEMY_SPEED = 2
BULLET_SPEED = 10
ENEMY_SPAWN_RATE = 60
PLAYER_WIDTH, PLAYER_HEIGHT = 50, 50
ENEMY_WIDTH, ENEMY_HEIGHT = 40, 40
BULLET_WIDTH, BULLET_HEIGHT = 10, 20

# ==============================================================================
# --- 2. Data Structure Definitions (The "State" - Pygame-Free) ---
# ==============================================================================


@dataclass(frozen=True)
class PlayerState:
    """The state of the player, using only primitive types."""

    x: float
    y: float
    health: int


@dataclass(frozen=True)
class EnemyState:
    """The state of a single enemy."""

    x: float
    y: float


@dataclass(frozen=True)
class BulletState:
    """The state of a single bullet."""

    x: float
    y: float


@dataclass(frozen=True)
class GameState:
    """A single object containing the entire state of the game."""

    player: PlayerState
    enemies: List[EnemyState] = field(default_factory=list)
    bullets: List[BulletState] = field(default_factory=list)
    score: int = 0
    is_game_over: bool = False
    spawn_timer: int = 0


# ==============================================================================
# --- 3. Functional Core (The "Rules Engine" - Truly Pure) ---
# ==============================================================================


class GameRules(Ruleset):
    """A collection of pure functions that contain all game logic."""

    @staticmethod
    def _rects_collide(x1, y1, w1, h1, x2, y2, w2, h2) -> bool:
        """A pure function to check for rectangle collision."""
        return x1 < x2 + w2 and x1 + w1 > x2 and y1 < y2 + h2 and y1 + h1 > y2

    @staticmethod
    def move_player(state: GameState, direction: str) -> GameState:
        """Calculates a new GameState after moving the player."""
        x, y = state.player.x, state.player.y
        if direction == "LEFT":
            x -= PLAYER_SPEED
        elif direction == "RIGHT":
            x += PLAYER_SPEED

        x = max(0, min(x, SCREEN_WIDTH - PLAYER_WIDTH))
        new_player_state = replace(state.player, x=x, y=y)
        return replace(state, player=new_player_state)

    @staticmethod
    def update_game_state(state: GameState) -> GameState:
        """The main pure function to advance the game state by one frame."""
        new_bullets = [
            replace(b, y=b.y - BULLET_SPEED)
            for b in state.bullets
            if b.y + BULLET_HEIGHT > 0
        ]
        new_enemies = [
            replace(e, y=e.y + ENEMY_SPEED)
            for e in state.enemies
            if e.y < SCREEN_HEIGHT
        ]

        collided_bullets, collided_enemies, new_score = set(), set(), state.score
        for i, b in enumerate(new_bullets):
            for j, e in enumerate(new_enemies):
                if GameRules._rects_collide(
                    b.x,
                    b.y,
                    BULLET_WIDTH,
                    BULLET_HEIGHT,
                    e.x,
                    e.y,
                    ENEMY_WIDTH,
                    ENEMY_HEIGHT,
                ):
                    collided_bullets.add(i)
                    collided_enemies.add(j)
                    new_score += 10

        final_bullets = [
            b for i, b in enumerate(new_bullets) if i not in collided_bullets
        ]
        final_enemies = [
            e for i, e in enumerate(new_enemies) if i not in collided_enemies
        ]

        is_game_over = state.is_game_over
        if not is_game_over:
            for enemy in final_enemies:
                if GameRules._rects_collide(
                    state.player.x,
                    state.player.y,
                    PLAYER_WIDTH,
                    PLAYER_HEIGHT,
                    enemy.x,
                    enemy.y,
                    ENEMY_WIDTH,
                    ENEMY_HEIGHT,
                ):
                    is_game_over = True
                    break

        new_spawn_timer = (state.spawn_timer + 1) % ENEMY_SPAWN_RATE
        if new_spawn_timer == 0:
            enemy_x = random.randint(0, SCREEN_WIDTH - ENEMY_WIDTH)
            final_enemies.append(EnemyState(x=enemy_x, y=-ENEMY_HEIGHT))

        return replace(
            state,
            bullets=final_bullets,
            enemies=final_enemies,
            score=new_score,
            is_game_over=is_game_over,
            spawn_timer=new_spawn_timer,
        )

    @staticmethod
    def shoot_bullet(state: GameState) -> GameState:
        """Creates a new game state with a new bullet."""
        if state.is_game_over:
            return state
        bullet_x = state.player.x + (PLAYER_WIDTH / 2) - (BULLET_WIDTH / 2)
        new_bullet = BulletState(x=bullet_x, y=state.player.y)
        return replace(state, bullets=state.bullets + [new_bullet])


# ==============================================================================
# --- 4. Stateful Shell (The "Pygame Manager") ---
# ==============================================================================


@ruleset_provider(GameRules)
class Game(StatefulEntity):
    """The main game class, delegating all logic to GameRules."""

    def __init__(self, screen: "Surface", clock: "Clock", font: "Font"):
        super().__init__()

        # Add this single, robust check at the beginning.
        if pygame is None:
            raise ImportError(
                "Pygame is not installed. Please install it with 'pip install pygame'"
            )

        self.screen = screen
        self.clock = clock
        self.font = font
        pygame.display.set_caption("PureShell Space Shooter")
        player_x = SCREEN_WIDTH / 2 - PLAYER_WIDTH / 2
        player_y = SCREEN_HEIGHT - 60
        self._state = GameState(player=PlayerState(x=player_x, y=player_y, health=100))

    @shell_method("_state", mutates=True)
    def update_game_state(self) -> None:
        raise NotImplementedError()

    @shell_method("_state", mutates=True)
    def move_player(self, direction: str) -> None:
        raise NotImplementedError()

    @shell_method("_state", mutates=True)
    def shoot_bullet(self) -> None:
        raise NotImplementedError()

    @side_effect_method
    def display(self):
        """Translates pure state into Pygame objects for drawing."""
        # This assert tells the linter that pygame cannot be None here.
        assert pygame is not None, "Pygame must be initialized before running the game."

        self.screen.fill((10, 10, 40))
        player_r = pygame.Rect(
            self._state.player.x, self._state.player.y, PLAYER_WIDTH, PLAYER_HEIGHT
        )
        pygame.draw.rect(self.screen, (0, 150, 255), player_r)
        for e in self._state.enemies:
            pygame.draw.rect(
                self.screen,
                (255, 50, 50),
                pygame.Rect(e.x, e.y, ENEMY_WIDTH, ENEMY_HEIGHT),
            )
        for b in self._state.bullets:
            pygame.draw.rect(
                self.screen,
                (255, 255, 100),
                pygame.Rect(b.x, b.y, BULLET_WIDTH, BULLET_HEIGHT),
            )

        score_text = self.font.render(
            f"Score: {self._state.score}", True, (255, 255, 255)
        )
        self.screen.blit(score_text, (10, 10))

        if self._state.is_game_over:
            over_text = self.font.render("GAME OVER", True, (255, 0, 0))
            over_rect = over_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
            self.screen.blit(over_text, over_rect)

        pygame.display.flip()

    @side_effect_method
    def run(self):
        """The main game loop."""
        assert pygame is not None, "Pygame must be initialized before running the game."

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    self.shoot_bullet()

            if not self._state.is_game_over:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_LEFT]:
                    self.move_player("LEFT")
                if keys[pygame.K_RIGHT]:
                    self.move_player("RIGHT")
                self.update_game_state()

            self.display()
            self.clock.tick(60)
        pygame.quit()


# ==============================================================================
# --- 5. Main Execution Block ---
# ==============================================================================
def main():
    """Main function to run the game."""
    assert pygame is not None, "Pygame must be initialized before running the game."

    pygame.init()  # Initialize Pygame
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    game = Game(screen=screen, clock=clock, font=font)
    game.run()


if __name__ == "__main__":
    main()

"""Unit tests for the Pygame example implementation."""

import unittest

# We only need to import the pure data and rules from the example
from examples.game_example import (
    GameState,
    PlayerState,
    EnemyState,
    BulletState,
    GameRules,
    PLAYER_SPEED,
    PLAYER_WIDTH,
)

# ==============================================================================
# --- Test Suite for Game Example (Now Mock-Free) ---
# ==============================================================================


class TestGameRules(unittest.TestCase):
    """
    Tests the pure functions in the GameRules class.
    Because the game logic is now totally decoupled from Pygame, these tests
    are simple, fast, and require no mocking.
    """

    def setUp(self):
        """Set up a basic game state for tests."""
        self.initial_player = PlayerState(x=400, y=500, health=100)
        self.initial_state = GameState(player=self.initial_player)

    def test_move_player(self):
        """Tests the pure player movement logic."""
        new_state = GameRules.move_player(self.initial_state, "LEFT")
        self.assertEqual(new_state.player.x, self.initial_state.player.x - PLAYER_SPEED)
        # Ensure other state is preserved
        self.assertEqual(new_state.enemies, self.initial_state.enemies)

    def test_shoot_bullet(self):
        """Tests the pure bullet creation logic."""
        new_state = GameRules.shoot_bullet(self.initial_state)
        self.assertEqual(len(new_state.bullets), 1)
        self.assertEqual(len(self.initial_state.bullets), 0)  # Immutability check
        # Check that bullet starts at player's center
        expected_bullet_x = self.initial_player.x + (PLAYER_WIDTH / 2) - 5
        self.assertEqual(new_state.bullets[0].x, expected_bullet_x)

    def test_update_game_state_collision(self):
        """Tests that collisions are detected and state is updated."""
        state_with_collision = GameState(
            player=self.initial_player,
            bullets=[BulletState(x=100, y=100)],
            enemies=[EnemyState(x=100, y=105)],  # Positioned to collide
        )
        new_state = GameRules.update_game_state(state_with_collision)

        # Both bullet and enemy should be removed
        self.assertEqual(len(new_state.bullets), 0)
        self.assertEqual(len(new_state.enemies), 0)
        self.assertEqual(new_state.score, 10)

    def test_update_game_state_player_collision(self):
        """Tests that player collision results in game over."""
        state_with_player_collision = GameState(
            player=self.initial_player,
            enemies=[EnemyState(x=self.initial_player.x, y=self.initial_player.y)],
        )
        new_state = GameRules.update_game_state(state_with_player_collision)
        self.assertTrue(new_state.is_game_over)


if __name__ == "__main__":
    unittest.main()

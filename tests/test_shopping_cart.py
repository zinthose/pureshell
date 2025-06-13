"""Unit tests for the ShoppingCart example implementation."""

import unittest

# import sys
# import os

# test_shopping_cart.py
# pylint: disable=line-too-long,protected-access,wrong-import-position

# Add the project root directory to the Python path
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from examples.shopping_cart_example import (
    CartItem,
    UserProfile,
    CartRules,
    ShoppingCart,
)

# ==============================================================================
# --- Test Suite for Shopping Cart ---
# ==============================================================================


class TestCartRules(unittest.TestCase):
    """Tests the pure functions in the CartRules class."""

    def test_calculate_total(self):
        """Tests the pure total calculation function."""
        items = [CartItem("A", 10.50), CartItem("B", 0.50)]
        self.assertEqual(CartRules.calculate_total(items), 11.00)
        self.assertEqual(CartRules.calculate_total([]), 0)

    def test_add_item(self):
        """Tests the pure item addition function."""
        initial_items = [CartItem("A", 1.00)]
        new_item = CartItem("B", 2.00)
        new_list = CartRules.add_item(initial_items, new_item)
        self.assertEqual(len(new_list), 2)
        self.assertEqual(new_list[-1].name, "B")
        # Ensure the original list was not mutated
        self.assertEqual(len(initial_items), 1)

    def test_is_valid(self):
        """Tests the pure cart validation logic."""
        adult = UserProfile("adult", 30)
        minor = UserProfile("minor", 15)
        age_restricted_item = CartItem("Beer", 5.00, requires_age_check=True)
        normal_item = CartItem("Bread", 3.00)

        self.assertTrue(CartRules.is_valid([age_restricted_item], adult))
        self.assertFalse(CartRules.is_valid([age_restricted_item], minor))
        self.assertTrue(CartRules.is_valid([normal_item], minor))
        self.assertTrue(CartRules.is_valid([], adult))


class TestShoppingCartIntegration(unittest.TestCase):
    """Tests the stateful ShoppingCart class."""

    def test_integration(self):
        """Tests the ShoppingCart class methods."""
        cart = ShoppingCart(user_id="test-user", age=25)
        self.assertEqual(cart.get_total(), 0)

        cart.add_item(CartItem("Milk", 3.00))
        self.assertEqual(len(cart._items), 1)
        self.assertEqual(cart.get_total(), 3.00)

        cart.add_item(CartItem("Cereal", 5.50))
        self.assertEqual(len(cart._items), 2)
        self.assertEqual(cart.get_total(), 8.50)

    def test_multi_attribute_method(self):
        """Tests a shell_method that uses multiple state attributes."""
        adult_cart = ShoppingCart(user_id="adult", age=30)
        minor_cart = ShoppingCart(user_id="minor", age=16)
        age_restricted_item = CartItem("Wine", 15.00, requires_age_check=True)

        adult_cart.add_item(age_restricted_item)
        minor_cart.add_item(age_restricted_item)

        self.assertTrue(adult_cart.is_valid_for_checkout())
        self.assertFalse(minor_cart.is_valid_for_checkout())


if __name__ == "__main__":
    unittest.main()

"""Example usage of the PureShell pattern for a Shopping Cart."""
# shopping_cart_example.py
from typing import List
from dataclasses import dataclass, field

from pureshell import (
    Ruleset, StatefulEntity, shell_method, ruleset_provider, side_effect_method
)

# ==============================================================================
# --- 1. Data Structure Definitions ---
# ==============================================================================

@dataclass(frozen=True)
class CartItem:
    """Represents an item in the shopping cart."""
    name: str
    price: float
    requires_age_check: bool = False

@dataclass(frozen=True)
class UserProfile:
    """Represents basic user profile data."""
    user_id: str
    age: int

# ==============================================================================
# --- 2. Functional Core / Rules Engine ---
# ==============================================================================

class CartRules(Ruleset):
    """A collection of pure functions for cart logic."""
    @staticmethod
    def add_item(items: List[CartItem], new_item: CartItem) -> List[CartItem]:
        """Pure function to add an item to a list of cart items."""
        return items + [new_item]

    @staticmethod
    def calculate_total(items: List[CartItem]) -> float:
        """Pure function to calculate the total price of all items in a list."""
        return sum(item.price for item in items)

    @staticmethod
    def is_valid(items: List[CartItem], profile: UserProfile) -> bool:
        """Checks if a cart is valid based on items and user profile."""
        if any(item.requires_age_check for item in items):
            return profile.age >= 21
        return True

# ==============================================================================
# --- 3. Stateful Shell ---
# ==============================================================================

@ruleset_provider(CartRules)
class ShoppingCart(StatefulEntity):
    """Manages a shopping cart by delegating logic to pure functions."""
    def __init__(self, user_id: str, age: int):
        """Initializes the shopping cart with user data."""
        self._items: List[CartItem] = []
        self._profile: UserProfile = UserProfile(user_id=user_id, age=age)
        print(f"ShoppingCart created for user {self._profile.user_id}.")

    @shell_method('_items', pure_func='calculate_total')
    def get_total(self) -> float:
        """Calculates the current total price of all items in the cart."""
        raise NotImplementedError()

    @shell_method('_items', mutates=True)
    def add_item(self, item: CartItem) -> None:
        """Adds a CartItem to the cart, mutating the internal items list."""
        raise NotImplementedError()

    @shell_method(('_items', '_profile'), pure_func='is_valid')
    def is_valid_for_checkout(self) -> bool:
        """Checks if the cart is valid based on items and user profile."""
        raise NotImplementedError()

    @side_effect_method
    def display(self):
        """Prints the current state of the shopping cart to the console."""
        print(f"\n--- Cart for: {self._profile.user_id} (Age: {self._profile.age}) ---")
        for item in self._items:
            print(f"- {item.name}: ${item.price:.2f}")
        print("-" * 20)
        print(f"Subtotal: ${self.get_total():.2f}")
        print(f"Valid for checkout: {self.is_valid_for_checkout()}")
        print("-" * 35 + "\n")

# ==============================================================================
# --- 4. Main Execution Block ---
# ==============================================================================

def main():
    """Main function to demonstrate the ShoppingCart example."""
    print("--- SHOPPING CART EXAMPLE ---")
    adult_cart = ShoppingCart(user_id="user-123", age=30)
    adult_cart.add_item(CartItem("Organic Apples", 4.99))
    adult_cart.add_item(CartItem("Craft Beer", 12.50, requires_age_check=True))
    adult_cart.display()


if __name__ == "__main__":
    main()

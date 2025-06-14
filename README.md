# 🐚 pureshell

A Python design pattern for creating Stateful Entities powered by a pure Functional Core. This library provides a simple, enforceable, and testable architecture for separating state management from business logic.

[![PyPI version](https://badge.fury.io/py/pureshell.svg)](https://badge.fury.io/py/pureshell)

## 🏛️ The "Stateful Shell" Pattern

At its core, `pureshell` helps you implement the "Functional Core, Stateful Shell" pattern. This means:

* **🧠 Functional Core**: All your complex business logic (e.g., game rules, business calculations) is written as pure, stateless functions. These functions are grouped into `Ruleset` classes and are incredibly easy to unit test.
* **🤖 Stateful Shell**: Your objects (`StatefulEntity` classes) act as simple "shells" that hold state. They delegate all their logic and calculations to the functional core, keeping the classes themselves clean, declarative, and free of implementation details.

This separation makes your system more robust, highly testable, and easier to reason about as it grows in complexity.

## ✨ Core Concepts

The framework is built around a few key components:

* `StatefulEntity`: A base class for your objects (`ShoppingCart`, `GameCharacter`, etc.). It enforces the pattern by ensuring no business logic is accidentally added to the class itself.
* `Ruleset`: A base class for your collections of pure functions (e.g., `CartRules`, `CharacterRules`). It enforces that all rules are defined as `@staticmethod`.
* `@ruleset_provider(RulesetClass)`: A class decorator that links a `StatefulEntity` to its corresponding `Ruleset`.
* `@shell_method(...)`: A method decorator that declaratively links a method on a `StatefulEntity` to a pure function in its `Ruleset`.
* `@side_effect_method`: A decorator to explicitly mark methods that perform I/O (like printing to the console or rendering graphics) as being exempt from the "pure logic" enforcement.

### New in version 0.2.0: Dynamic Ruleset Injection

You can now inject a `Ruleset` instance directly when creating a `StatefulEntity`. This allows for more flexible and dynamic behavior, especially useful for scenarios like:

* **Strategy Pattern:** Easily switch between different sets of rules at runtime.
* **Testing:** Inject mock or simplified rulesets for testing specific behaviors.
* **Configuration-driven Behavior:** Load different rulesets based on configuration files or user settings.

If a `ruleset_instance` is provided during `StatefulEntity` instantiation, it will be used instead of the one specified by the `@ruleset_provider` decorator.

```python
# Example of dynamic ruleset injection
from pureshell import StatefulEntity, Ruleset, shell_method

class BehaviorA(Ruleset):
    @staticmethod
    def act(state_data: dict) -> dict:
        print("Performing Action A")
        return {**state_data, "action_taken": "A"}

class BehaviorB(Ruleset):
    @staticmethod
    def act(state_data: dict) -> dict:
        print("Performing Action B")
        return {**state_data, "action_taken": "B"}

class MyEntity(StatefulEntity):
    def __init__(self, initial_state: dict, ruleset_instance: Ruleset = None):
        # StatefulEntity.__init__ now handles initial_state and ruleset_instance
        super().__init__(initial_state, ruleset_instance)

    @shell_method("state_data", pure_func="act", mutates=True)
    def perform_action(self) -> None:
        pass # Logic delegated to ruleset's 'act' method

# Create entity with default behavior (if a @ruleset_provider is set)
# entity_default = MyEntity(initial_state={})

# Create entity with BehaviorA
entity_a = MyEntity(initial_state={"state_data": {}}, ruleset_instance=BehaviorA())
entity_a.perform_action() # Will use BehaviorA.act

# Create entity with BehaviorB
entity_b = MyEntity(initial_state={"state_data": {}}, ruleset_instance=BehaviorB())
entity_b.perform_action() # Will use BehaviorB.act
```

## 🚀 Installation

To use `pureshell` in your project, it's highly recommended to work within a virtual environment.

1. **Create and activate a virtual environment:**

   ```bash
   # Windows
   python -m venv .venv
   .venv\\Scripts\\activate

   # macOS/Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install from PyPI (for users of the library):**

   ```bash
   pip install pureshell
   ```

   Alternatively, if you have a `requirements.txt` file that includes `pureshell`:

   ```bash
   pip install -r requirements.txt
   ```

3. **For development (if you've cloned this repository):**

   Install the project and its development dependencies:

   ```bash
   pip install -e .
   pip install -r requirements-dev.txt
   ```

   This will install the project in editable mode and all tools needed for testing, linting, formatting, etc.

## 🚀 Usage

Here's a practical example of defining a `ShoppingCart` using the `pureshell` pattern. This example is available in `examples/shopping_cart_example.py`.

**1. Define your data structures and pure functions:**

First, we define our data classes and a `Ruleset` containing all the business logic as pure, static methods.

```python
# In examples/shopping_cart_example.py
from dataclasses import dataclass
from typing import List
from pureshell import Ruleset

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
```

**2. Define your stateful entity:**

Next, create the `ShoppingCart` class. It inherits from `StatefulEntity`, holds the state, and uses `@shell_method` to declaratively link its methods to the pure functions in `CartRules`.

```python
# In examples/shopping_cart_example.py
from pureshell import StatefulEntity, shell_method, ruleset_provider, side_effect_method

@ruleset_provider(CartRules)
class ShoppingCart(StatefulEntity):
    """Manages a shopping cart by delegating logic to pure functions."""
    def __init__(self, user_id: str, age: int):
        self._items: List[CartItem] = []
        self._profile: UserProfile = UserProfile(user_id=user_id, age=age)

    @shell_method('_items', pure_func='calculate_total')
    def get_total(self) -> float:
        """Calculates the current total price of all items."""
        raise NotImplementedError()

    @shell_method('_items', mutates=True) # Infers pure_func='add_item'
    def add_item(self, item: CartItem) -> None:
        """Adds a CartItem to the cart."""
        raise NotImplementedError()

    @shell_method(('_items', '_profile'), pure_func='is_valid')
    def is_valid_for_checkout(self) -> bool:
        """Checks if the cart is valid for the user."""
        raise NotImplementedError()

    @side_effect_method
    def display(self):
        """Prints the current state of the cart (a permitted side-effect)."""
        # ... implementation for printing state ...
```

**3. Use your object:**

Now you can use the `ShoppingCart` object. Its methods are simple to call, while the complex logic is handled by the functional core.

```python
# --- In your main script ---
adult_cart = ShoppingCart(user_id="user-123", age=30)
adult_cart.add_item(CartItem("Organic Apples", 4.99))
adult_cart.add_item(CartItem("Craft Beer", 12.50, requires_age_check=True))

print(f"Total: ${adult_cart.get_total():.2f}")
# Output: Total: $17.49

print(f"Is valid for checkout: {adult_cart.is_valid_for_checkout()}")
# Output: Is valid for checkout: True
```

### 🛑 Why raise NotImplementedError()?

You'll notice that the decorated methods in the `StatefulEntity` have `raise NotImplementedError()` as their implementation. This is because the `@shell_method` decorator replaces the method with its own logic. This practice ensures that if the decorator is ever misconfigured or accidentally removed, the program will fail immediately and loudly, preventing logic from being silently ignored.

In addition, this addresses linter warnings that would be raised if `pass` or ellipsis (`...`) were used instead.

## 🎮 Running the Examples

This repository includes complete, runnable examples to demonstrate the pattern. A helper script is provided to easily run them.

First, ensure you have installed the project in editable mode and the development dependencies (see [🚀 Installation](#-installation)).

Then, run the examples module:

```bash
python -m examples.run
```

This will present a menu where you can choose between:

* **Shopping Cart**: The simple e-commerce example detailed above.
* **Pygame Space Shooter**: A more advanced example showing how `pureshell` can be used to completely separate game logic from the Pygame rendering engine, making the logic highly testable.

## ✅ Running Tests & Quality Checks

This project uses `pytest` for testing, `flake8` for linting, `black` for formatting, `mypy` for type checking, and `pre-commit` to automate these checks.

1. **Ensure development dependencies are installed:**

   ```bash
   pip install -r requirements-dev.txt
   ```

2. **Run all tests with coverage:**

   ```bash
   pytest
   ```

   Coverage reports are generated in HTML format in the `htmlcov/` directory and also printed to the console.

3. **Run linters and formatters manually:**

   ```bash
   flake8 .
   black .
   isort .
   mypy .
   ```

4. **Use pre-commit hooks (recommended):**

   Pre-commit hooks will automatically run checks before each commit.

   ```bash
   pre-commit install
   ```

   Now, `flake8`, `black`, `isort`, and `mypy` will run on staged files automatically when you commit. If they find issues, the commit will be aborted, allowing you to fix them.

## 📚 Building Documentation

Documentation is built using Sphinx.

1. **Ensure development dependencies are installed:**

   ```bash
   pip install -r requirements-dev.txt
   ```

2. **Build the HTML documentation:**

   ```bash
   sphinx-build -b html docs docs/_build/html
   ```

   The generated HTML will be in `docs/_build/html/index.html`.

## CI Pipeline

This project uses GitHub Actions for Continuous Integration. The workflow is defined in `.github/workflows/ci.yml` and includes:

* Linting with Flake8
* Formatting checks with Black and isort
* Type checking with MyPy
* Running tests with Pytest and generating coverage reports
* Uploading coverage reports to Codecov (if `CODECOV_TOKEN` is set in repository secrets)

## 🗺️ Roadmap / Future Iterations

The following features are planned for future versions of `pureshell` to enhance its flexibility and power for more advanced use cases:

* **Dynamic Ruleset Injection**: Allow a `Ruleset` to be injected at instantiation time (`__init__`) rather than just at the class level. This would enable different instances of the same entity to use different logic (e.g., "Easy" vs. "Hard" mode AI).

* **Advanced Error Handling**: Add a mechanism to the `@shell_method` wrapper to gracefully catch and handle exceptions raised by pure functions, preventing crashes and allowing for more resilient entities.

* **Asynchronous Operations**: Introduce support for `async/await` within the framework, allowing `shell_method` to call and await asynchronous pure functions. This is essential for I/O-bound operations.

* **Memoization for Performance**: Add an optional caching (`memoization`) feature to read-only `@shell_method` calls. This would store and reuse the results of expensive calculations, boosting performance in read-heavy scenarios.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any bugs, feature requests, or suggestions.

## 📄 License

This project is licensed under the MIT License.

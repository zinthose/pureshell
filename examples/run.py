"""
A user-friendly entry point to run the examples for the pureshell package.
This script handles path setup and provides a simple menu.
"""

import importlib
import os
import sys


def main():
    """
    Sets up the path, displays a menu, and runs the selected example.
    """
    # Add the project root to the Python path to allow importing the 'pureshell'
    # package and the 'examples' modules correctly.
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(project_root))  # Corrected line

    examples = {
        "1": ("examples.shopping_cart_example", "Shopping Cart"),
        "2": ("examples.game_example", "Pygame Space Shooter"),
        "3": ("examples.dynamic_behavior_example", "Dynamic Behavior Bot"),
    }

    while True:
        print("\n--- PureShell Examples ---")
        for key, (_, name) in examples.items():
            print(f"{key}: {name}")
        print("q: Quit")

        choice = input("Select an example to run: ")

        if choice.lower() == "q":
            break

        if choice in examples:
            module_name, example_name = examples[choice]
            print(f"\n--- Running: {example_name} ---\n")
            try:

                module = importlib.import_module(module_name)
                # Assuming each example script has a main() function
                if hasattr(module, "main"):
                    module.main()
                else:
                    print(
                        f"Error: Example '{module_name}' does "
                        "not have a main() function."
                    )
            except ImportError as e:
                print(f"Error importing example: {e}")
            print(f"\n--- Finished: {example_name} ---")
        else:
            print("Invalid selection. Please try again.")


if __name__ == "__main__":
    main()

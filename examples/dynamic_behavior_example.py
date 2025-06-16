"""
Example demonstrating dynamic ruleset injection for a configurable bot.
"""

from dataclasses import dataclass, field

from pureshell import Ruleset, StatefulEntity, shell_method, side_effect_method


# ---------------------
# 1. Define Data Structures
# ---------------------
@dataclass
class BotState:
    """Represents the internal state of our bot."""

    name: str
    energy_level: int = 100
    mood: str = "neutral"
    log: list[str] = field(default_factory=list)


# ---------------------
# 2. Define Rulesets
# ---------------------
class FriendlyBotRules(Ruleset):
    """Rules for a friendly bot."""

    @staticmethod
    def respond(state: BotState, stimulus: str) -> BotState:  # Return type changed
        """
        Generates a friendly response to a stimulus and updates the bot's state.

        Args:
            state: The current state of the bot.
            stimulus: The input stimulus (e.g., a user message).

        Returns:
            The updated bot state.
        """
        state.log.append(f"Friendly response to: {stimulus}")
        if "hello" in stimulus.lower():
            state.mood = "happy"
            # Return the modified state
        else:
            state.mood = "curious"
        return state  # Return the modified state

    @staticmethod
    def perform_action(state: BotState) -> BotState:  # Return type changed
        """
        Performs a friendly action and updates the bot's state.

        Args:
            state: The current state of the bot.

        Returns:
            The updated bot state.
        """
        state.log.append("Friendly action performed.")
        state.energy_level -= 5
        # Return the modified state
        return state


class AggressiveBotRules(Ruleset):
    """Rules for an aggressive bot."""

    @staticmethod
    def respond(state: BotState, stimulus: str) -> BotState:  # Return type changed
        """
        Generates an aggressive response to a stimulus and updates the bot's state.

        Args:
            state: The current state of the bot.
            stimulus: The input stimulus (e.g., a user message).

        Returns:
            The updated bot state.
        """
        state.log.append(f"Aggressive response to: {stimulus}")
        if "hello" in stimulus.lower():
            state.mood = "annoyed"
        else:
            state.mood = "hostile"
        return state  # Return the modified state

    @staticmethod
    def perform_action(state: BotState) -> BotState:  # Return type changed
        """
        Performs an aggressive action and updates the bot's state.

        Args:
            state: The current state of the bot.

        Returns:
            The updated bot state.
        """
        state.log.append("Aggressive action performed.")
        state.energy_level -= 15  # Aggressive actions take more energy
        # Return the modified state
        return state


# ---------------------
# 3. Define Stateful Entity
# ---------------------
class ConfigurableBot(StatefulEntity):
    """A bot whose behavior can be configured by injecting a ruleset."""

    def __init__(self, name: str, rules_instance: Ruleset):
        """
        Initializes the ConfigurableBot.

        Args:
            name: The name of the bot.
            rules_instance: An instance of a Ruleset class that defines the
                            bot's behavior.
        """
        super().__init__()
        self.state = BotState(name=name)
        self._instance_rules = rules_instance  # Dynamic ruleset injection

    @shell_method("state", mutates=True)  # Infers pure_func='respond'
    def respond(self, stimulus: str) -> None:
        # Return type is None for mutating shell methods
        """
        Processes a stimulus and generates a response based on the injected ruleset.

        This method is a shell that delegates to the 'respond' method of the
        injected ruleset. The bot's state is mutated accordingly.

        Args:
            stimulus: The input stimulus (e.g., a user message).
        """
        # The actual logic is in the injected ruleset's 'respond' method.
        raise NotImplementedError()

    @shell_method("state", mutates=True)  # Infers pure_func='perform_action'
    def perform_action(self) -> None:  # Return type is None for mutating shell methods
        """
        Performs an action based on the injected ruleset.

        This method is a shell that delegates to the 'perform_action' method of the
        injected ruleset. The bot's state is mutated accordingly.
        """
        raise NotImplementedError()

    @side_effect_method
    def display_status(self) -> None:
        """Prints the current status of the bot to the console."""
        print(f"--- {self.state.name} Status ---")
        print(f"  Mood: {self.state.mood}")
        print(f"  Energy: {self.state.energy_level}")
        print(f"  Log: {self.state.log}")
        print("------------------------")


# ---------------------
# 4. Demonstrate Usage
# ---------------------
def main():
    """Demonstrates the configurable bot with different rulesets."""
    print("\n--- Creating a Friendly Bot ---")
    friendly_rules = FriendlyBotRules()
    friendly_bot = ConfigurableBot(name="Buddy", rules_instance=friendly_rules)

    friendly_bot.display_status()
    # The shell methods now return None, so we don't print their result directly.
    friendly_bot.respond("Hello there!")
    friendly_bot.display_status()
    friendly_bot.perform_action()
    friendly_bot.display_status()

    print("\n--- Creating an Aggressive Bot ---")
    aggressive_rules = AggressiveBotRules()
    aggressive_bot = ConfigurableBot(name="Spike", rules_instance=aggressive_rules)

    aggressive_bot.display_status()
    aggressive_bot.respond("Hello?")
    aggressive_bot.display_status()
    aggressive_bot.perform_action()
    aggressive_bot.display_status()


if __name__ == "__main__":
    main()

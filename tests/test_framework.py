"""Unit tests for the core PureShell framework enforcement."""

import unittest

from pureshell import (
    Ruleset,
    StatefulEntity,
    ruleset_provider,
    shell_method,
    RulesetProviderError,  # Import new error type
    PureFunctionError,  # Import new error type
    LiveAttributeError,  # Import new error type
)

# test_framework.py
# pylint: disable=line-too-long,protected-access,wrong-import-position

# Add the project root directory to the Python path
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ==============================================================================
# --- Test Suite for Core Framework ---
# ==============================================================================


class TestPatternEnforcement(unittest.TestCase):
    """Tests the enforcement mechanisms of the base classes."""

    def test_stateful_entity_enforcement(self):
        """Ensures StatefulEntity rejects classes with raw business logic."""
        # Updated regex to match the more specific error message from StatefulEntity
        expected_error_regex = r"Class \'.*\' has an implemented method \'.*\'"
        with self.assertRaisesRegex(TypeError, expected_error_regex):
            # This class definition should fail at import time because it violates
            # the StatefulEntity contract.
            class RogueEntity(StatefulEntity):  # pylint: disable=unused-variable
                """An invalid entity with logic in a method."""

                def rogue_method(self):
                    """This should not be allowed."""
                    return 1 + 1

    def test_ruleset_enforcement(self):
        """Ensures Ruleset rejects classes with non-static methods."""
        with self.assertRaisesRegex(TypeError, "has a non-static method 'rogue_rule'"):
            # This class definition should fail because its method is not static.
            class RogueRules(Ruleset):  # pylint: disable=unused-variable
                """An invalid ruleset."""

                def rogue_rule(self):
                    """This should not be allowed."""
                    return True


class TestDynamicRulesetFeatures(unittest.TestCase):
    """Tests features related to dynamic ruleset assignment."""

    def test_dynamic_ruleset_injection(self):
        """Tests that rulesets can be injected at instantiation time."""

        class RulesA(Ruleset):
            @staticmethod
            def get_value(data: int) -> str:
                return f"A:{data * 2}"

        class RulesB(Ruleset):
            @staticmethod
            def get_value(data: int) -> str:
                return f"B:{data * 3}"

        @ruleset_provider(RulesA)  # Default class-level ruleset
        class MyEntity(StatefulEntity):
            def __init__(
                self, initial_data: int, rules_instance: Ruleset | None = None
            ):
                self.data = initial_data
                # Dynamically set instance rules if provided
                if rules_instance:
                    self._instance_rules = rules_instance
                # If not, it will use RulesA from @ruleset_provider
                # Or if _instance_rules is explicitly set to None, it also uses RulesA

            @shell_method("data")  # Infers pure_func=\'get_value\'
            def get_value(self) -> str:
                raise NotImplementedError()

        class EntityNoDefaultRules(StatefulEntity):
            def __init__(
                self, initial_data: int, rules_instance: Ruleset | None = None
            ):
                self.data = initial_data
                if rules_instance:
                    self._instance_rules = rules_instance

            @shell_method("data")
            def get_value(self) -> str:
                raise NotImplementedError()

        # Test with instance-specific rules
        entity_a_explicit = MyEntity(10, RulesA())
        self.assertEqual(entity_a_explicit.get_value(), "A:20")

        entity_b_injected = MyEntity(10, RulesB())
        self.assertEqual(entity_b_injected.get_value(), "B:30")

        # Test fallback to class-level ruleset
        entity_a_default = MyEntity(10)  # No instance rules, should use RulesA
        self.assertEqual(entity_a_default.get_value(), "A:20")

        # Test explicit None for instance_rules falls back to class-level
        entity_a_explicit_none = MyEntity(10, rules_instance=None)
        self.assertEqual(entity_a_explicit_none.get_value(), "A:20")

        # Test entity with no default class-level rules
        entity_no_default_with_rules = EntityNoDefaultRules(5, RulesA())
        self.assertEqual(entity_no_default_with_rules.get_value(), "A:10")

        # Test error when no ruleset is available at all
        entity_no_rules_at_all = EntityNoDefaultRules(5)
        # Updated regex to match the new error message format
        expected_error_regex = (
            r"PureShell: Rules provider not found for "
            r"'EntityNoDefaultRules' "
            r"when resolving shell method 'get_value'\. "
            r"Use @ruleset_provider or set 'self\._instance_rules'\."
        )

        # Use new error type
        with self.assertRaisesRegex(RulesetProviderError, expected_error_regex):
            entity_no_rules_at_all.get_value()

    def test_missing_pure_function_error(self):
        """Tests that PureFunctionError is raised for a non-existent pure function."""

        class SimpleRules(Ruleset):
            @staticmethod
            def existing_rule(data: int) -> int:
                return data * 10

        @ruleset_provider(SimpleRules)
        class EntityWithMissingPureFunc(StatefulEntity):
            def __init__(self, val: int):
                self.value = val

            # This shell_method points to a pure function that does not exist
            @shell_method("value", pure_func="non_existent_rule")
            def calculate(self) -> int:
                raise NotImplementedError()

        entity = EntityWithMissingPureFunc(5)
        # Corrected regex to match the actual error message from __init__.py
        expected_error_regex = (
            r"PureShell: Pure function 'non_existent_rule' not found on "
            r"rules provider 'SimpleRules' "
            r"\(type: type\) "
            r"for shell method in 'EntityWithMissingPureFunc'\. "
        )
        with self.assertRaisesRegex(PureFunctionError, expected_error_regex):
            entity.calculate()  # This call should trigger the PureFunctionError

    def test_missing_live_attribute_error(self):
        """Tests that LiveAttributeError is raised for a non-existent live attribute."""

        class SimpleRules(Ruleset):
            @staticmethod
            def process_data(data: int) -> int:  # Added a dummy pure function
                return data

        @ruleset_provider(SimpleRules)
        class EntityWithMissingAttribute(StatefulEntity):
            def __init__(self):
                # self.actual_data is intentionally not defined
                pass

            # This shell_method points to a live_attribute that does not exist
            @shell_method("non_existent_data", pure_func="process_data")
            def get_processed_data(self) -> int:
                raise NotImplementedError()

        entity = EntityWithMissingAttribute()
        # Corrected regex to match the actual error message from __init__.py
        expected_error_regex = (
            r"PureShell: Live attribute 'non_existent_data' not found on "
            r"instance of 'EntityWithMissingAttribute' "
            r"when calling shell method\."
        )
        with self.assertRaisesRegex(LiveAttributeError, expected_error_regex):
            # This call should trigger the LiveAttributeError
            entity.get_processed_data()


if __name__ == "__main__":
    unittest.main()

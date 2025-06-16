"""Unit tests for the core PureShell framework enforcement."""

import unittest
import asyncio  # Add asyncio import

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
# pylint: disable=line-too-long,protected-access,wrong-import-position,
# pylint: disable=missing-class-docstring,missing-function-docstring


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


# =============================================================================
# --- Test Suite for Async Features ---
# =============================================================================
class TestAsyncFeatures(unittest.IsolatedAsyncioTestCase):
    """Tests asynchronous functionality including edge cases and error handling."""

    async def test_async_shell_method_execution(self):
        """Ensures async shell methods execute and return correct values."""

        class AsyncRules(Ruleset):
            @staticmethod
            async def process_async(data: int) -> str:
                await asyncio.sleep(0.01)  # Simulate async work
                return f"Async:{data * 2}"

        @ruleset_provider(AsyncRules)
        class AsyncEntity(StatefulEntity):
            def __init__(self, val: int):
                self.value = val

            @shell_method("value", pure_func="process_async")
            async def get_processed_value(self) -> str:
                raise NotImplementedError()

        entity = AsyncEntity(10)
        result = await entity.get_processed_value()
        self.assertEqual(result, "Async:20")

    async def test_async_mutation_shell_method(self):
        """Tests that async shell methods can mutate state correctly."""

        class AsyncMutationRules(Ruleset):
            @staticmethod
            async def increment_async(data: int, amount: int) -> int:
                await asyncio.sleep(0.01)
                return data + amount

        @ruleset_provider(AsyncMutationRules)
        class AsyncMutableEntity(StatefulEntity):
            def __init__(self, initial_value: int):
                self.value = initial_value

            @shell_method("value", pure_func="increment_async", mutates=True)
            async def increment(self, amount: int) -> None:
                raise NotImplementedError()

        entity = AsyncMutableEntity(5)
        await entity.increment(3)
        self.assertEqual(entity.value, 8)
        # Mutating methods should return None
        self.assertIsNone(await entity.increment(2))
        self.assertEqual(entity.value, 10)

    async def test_async_shell_method_with_no_rules_provider(self):
        """Tests RulesetProviderError for async method if no ruleset is found."""

        class EntityNeedsAsyncRules(StatefulEntity):
            def __init__(self, val: int):
                self.value = val

            @shell_method("value", pure_func="some_async_rule")
            async def get_value_async(self) -> str:
                raise NotImplementedError()

        entity = EntityNeedsAsyncRules(10)
        expected_error_regex = (
            r"PureShell: Rules provider not found for "
            r"'EntityNeedsAsyncRules' "
            r"when resolving shell method 'some_async_rule'\. "
            r"Use @ruleset_provider or set 'self\._instance_rules'\."
        )
        with self.assertRaisesRegex(RulesetProviderError, expected_error_regex):
            await entity.get_value_async()

    async def test_async_shell_method_missing_pure_function(self):
        """Tests PureFunctionError for async method if pure function is missing."""

        class DummyAsyncRules(Ruleset):
            @staticmethod
            async def existing_async_rule(data: int) -> int:
                return data  # pragma: no cover

        @ruleset_provider(DummyAsyncRules)
        class EntityWithMissingAsyncPureFunc(StatefulEntity):
            def __init__(self, val: int):
                self.value = val

            @shell_method("value", pure_func="non_existent_async_rule")
            async def calculate_async(self) -> int:
                raise NotImplementedError()

        entity = EntityWithMissingAsyncPureFunc(5)
        expected_error_regex = (
            r"PureShell: Pure function 'non_existent_async_rule' not found on "
            r"rules provider 'DummyAsyncRules' "
            r"\(type: type\) "
            r"for shell method in 'EntityWithMissingAsyncPureFunc'\. "
        )
        with self.assertRaisesRegex(PureFunctionError, expected_error_regex):
            await entity.calculate_async()

    async def test_async_shell_method_missing_live_attribute(self):
        """Tests LiveAttributeError for async method if live attribute is missing."""

        class AnotherAsyncRules(Ruleset):
            @staticmethod
            async def process_something_async(data: int) -> int:
                return data  # pragma: no cover

        @ruleset_provider(AnotherAsyncRules)
        class EntityWithMissingAsyncAttribute(StatefulEntity):
            def __init__(self):
                pass  # Intentionally not defining 'actual_data'

            @shell_method(
                "non_existent_async_data", pure_func="process_something_async"
            )
            async def get_data_async(self) -> int:
                raise NotImplementedError()

        entity = EntityWithMissingAsyncAttribute()
        expected_error_regex = (
            r"PureShell: Live attribute 'non_existent_async_data' not found on "
            r"instance of 'EntityWithMissingAsyncAttribute' "
            r"when calling shell method\."
        )
        with self.assertRaisesRegex(LiveAttributeError, expected_error_regex):
            await entity.get_data_async()

    async def test_mixed_sync_async_rules_resolution(self):
        """Tests that sync/async shell methods correctly resolve pure functions."""
        # This test explores if a synchronous shell_method can correctly resolve
        # a synchronous pure_function from a ruleset that also contains async methods,
        # and if an asynchronous shell_method can resolve an async pure_function
        # from a ruleset that also contains sync methods. The key is that the specific
        # pure_function being called matches the sync/async nature of the shell_method.

        class MixedRules(Ruleset):
            @staticmethod
            def sync_rule(data: int) -> str:
                return f"Sync:{data}"

            @staticmethod
            async def async_rule(data: int) -> str:
                await asyncio.sleep(0.01)
                return f"Async:{data}"

        @ruleset_provider(MixedRules)
        class MixedEntity(StatefulEntity):
            def __init__(self, val: int):
                self.value = val

            @shell_method("value", pure_func="sync_rule")
            def get_sync_value(self) -> str:  # Sync shell method
                raise NotImplementedError()

            @shell_method("value", pure_func="async_rule")
            async def get_async_value(self) -> str:  # Async shell method
                raise NotImplementedError()

        entity = MixedEntity(100)

        # Test sync shell method calling sync pure function
        sync_result = entity.get_sync_value()
        self.assertEqual(sync_result, "Sync:100")

        # Test async shell method calling async pure function
        async_result = await entity.get_async_value()
        self.assertEqual(async_result, "Async:100")

    async def test_async_shell_method_calling_sync_pure_function_error(self):
        """Tests TypeError for async shell_method calling sync pure_function."""

        # This scenario should ideally be caught by the framework,
        # as an async shell_method expects an awaitable from the pure_function.
        class SyncPureFuncRules(Ruleset):
            @staticmethod
            def strictly_sync_rule(data: int) -> str:
                return f"SyncData:{data}"

        @ruleset_provider(SyncPureFuncRules)
        class EntityAsyncShellSyncPure(StatefulEntity):
            def __init__(self, val: int):
                self.value = val

            @shell_method("value", pure_func="strictly_sync_rule")
            async def get_value_async_expecting_awaitable(self) -> str:
                # This shell method is async, but pure_func is sync
                raise NotImplementedError()

        entity = EntityAsyncShellSyncPure(7)
        # The PureShellMethod wrapper should raise a TypeError because it tries to
        # await a non-awaitable (the result of the sync pure function).
        with self.assertRaises(TypeError) as cm:
            await entity.get_value_async_expecting_awaitable()

        # Check that the error message indicates an issue with awaiting a non-coroutine
        # This message comes from Python's asyncio internals
        # when `await` is used on non-awaitable
        self.assertIn(
            "object str can't be used in 'await' expression", str(cm.exception).lower()
        )


if __name__ == "__main__":
    unittest.main()

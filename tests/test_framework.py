"""Unit tests for the core PureShell framework enforcement."""

import unittest

from pureshell import StatefulEntity, Ruleset

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
        with self.assertRaisesRegex(TypeError, "has a method 'rogue_method'"):
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


if __name__ == "__main__":
    unittest.main()

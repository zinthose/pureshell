"""PureShell: A Python Design Pattern for Stateful Entities with Pure Functions"""

# __init__.py
# pylint: disable=line-too-long,protected-access
from typing import Any, Callable, Generic, TypeVar, Union, cast, overload

# ==============================================================================
# --- 1. Generic Type Variables & Metaprogramming Tools ---
# These are the core tools that power the pattern.
# ==============================================================================

_ReturnType = TypeVar("_ReturnType")  # pylint: disable=invalid-name
_sentinel = object()  # A unique sentinel value for default arguments


class GetAttrNotFoundError(AttributeError):
    """Custom error raised when an attribute is not found in the rules provider."""

    def __init__(self, attr_name: str, instance: Any):
        super().__init__(
            f"Attribute '{attr_name}' listed in @shell_method not"
            f" found on instance of '{instance.__class__.__name__}'."
        )


class PureShellMethod(Generic[_ReturnType]):
    """
    A generic descriptor that creates a "lazy" partial function.

    It resolves the pure function it's linked to at call time,
    allowing it to fetch live data from the instance it's attached to.
    """

    def __init__(
        self,
        func_or_name: Callable[..., Any] | str,
        live_attr_names: str | tuple[str, ...],
        mutates: bool = False,
    ):
        """
        Initializes the PureShellMethod descriptor.

        Args:
            func_or_name: The pure function to call, or its name as a string.
            live_attr_names: A string or tuple of strings specifying the instance
                             attributes to pass as arguments to the pure function.
            mutates: If True, the method is treated as a state mutation. The
                     result of the pure function will overwrite the first
                     live attribute, and the method will return None.
        """
        self.func_or_name = func_or_name
        self.live_attr_names = (
            (live_attr_names,) if isinstance(live_attr_names, str) else live_attr_names
        )
        self.mutates = mutates

    @overload
    def __get__(
        self, instance: None, owner: type
    ) -> "PureShellMethod[_ReturnType]": ...

    @overload
    def __get__(
        self, instance: object, owner: type
    ) -> Callable[..., Union[_ReturnType, None]]: ...

    def __get__(
        self, instance: object | None, owner: type
    ) -> Union[Callable[..., Union[_ReturnType, None]], "PureShellMethod[_ReturnType]"]:
        """
        The core of the descriptor protocol, called on attribute access.

        When accessed on an instance, it returns a callable `wrapper` that,
        when called, will execute the pure function with live instance data.
        """
        if instance is None:
            return self

        def wrapper(*args: Any, **kwargs: Any) -> _ReturnType | None:
            """Wraps the pure function call, injecting live state."""
            actual_func: Callable[..., Any]
            # Resolve the pure function at call time
            if isinstance(self.func_or_name, str):
                rules_source: Any | None = None
                # 1. Check for instance-specific rules
                if (
                    hasattr(instance, "_instance_rules")
                    and getattr(instance, "_instance_rules") is not None
                ):
                    rules_source = getattr(instance, "_instance_rules")
                # 2. Fallback to class-level rules
                elif (
                    hasattr(instance.__class__, "_rules")
                    and getattr(instance.__class__, "_rules") is not None
                ):
                    rules_source = getattr(instance.__class__, "_rules")

                if rules_source is None:
                    err_msg = (
                        f"Instance of '{instance.__class__.__name__}' uses "
                        f"string-based shell method '{self.func_or_name}' but has no "
                        f"rules provider. Assign to 'self._instance_rules' in "
                        f"__init__ or use @ruleset_provider."
                    )
                    raise AttributeError(err_msg)
                try:
                    actual_func = getattr(rules_source, self.func_or_name)
                except AttributeError as e:
                    rules_name = (
                        rules_source.__class__.__name__
                        if not isinstance(rules_source, type)
                        else rules_source.__name__
                    )
                    err_msg = (
                        f"Pure function '{self.func_or_name}' not found on rules "
                        f" provider '{rules_source}'. Ensure defined in '{rules_name}'."
                    )
                    raise AttributeError(err_msg) from e
            else:  # func_or_name is a direct callable
                actual_func = self.func_or_name

            live_data_values = []
            for name in self.live_attr_names:
                attr = getattr(instance, name, _sentinel)
                if attr is _sentinel:
                    raise GetAttrNotFoundError(name, instance)
                live_data_values.append(attr)
            mutating_attr_index = 0 if self.mutates else -1
            result = actual_func(*live_data_values, *args, **kwargs)

            if self.mutates:
                setattr(instance, self.live_attr_names[mutating_attr_index], result)
                return None

            return cast(_ReturnType | None, result)

        return wrapper


def ruleset_provider(rules_cls: type) -> Callable[[type], type]:
    """A class decorator that registers a 'rules' class for an entity."""

    def decorator(entity_cls: type) -> type:
        """Attaches the ruleset class to the entity class."""
        setattr(entity_cls, "_rules", rules_cls)  # Use setattr for dynamic assignment
        return entity_cls

    return decorator


def shell_method(
    live_attr_names: str | tuple[str, ...],
    pure_func: Callable[..., Any] | str | None = None,
    mutates: bool = False,
) -> Callable[[Callable[..., Any]], PureShellMethod[Any]]:
    """
    A method decorator that links a method to a pure function.

    This decorator replaces a placeholder method in a StatefulEntity with a
    PureShellMethod descriptor, configuring the link between the stateful shell and
    the functional core. It can infer the pure function's name from the method
    it decorates or use an explicitly provided name/function.
    """

    def decorator(func_placeholder: Callable[..., Any]) -> PureShellMethod[Any]:
        """Creates and returns the configured PureShellMethod descriptor."""
        # If pure_func is not provided, use the placeholder's name by convention.
        func_or_name = pure_func or func_placeholder.__name__
        return PureShellMethod(func_or_name, live_attr_names, mutates)

    return decorator


def side_effect_method(func: Callable[..., Any]) -> Callable[..., Any]:
    """A decorator to explicitly mark a method as having side effects."""
    # Tag the function with a special attribute for the enforcement hook to find.
    setattr(func, "_is_side_effect", True)
    return func


class Ruleset:
    """A base class that ENFORCES that all methods in a ruleset are static."""

    def __init_subclass__(cls, **kwargs: Any) -> None:  # Added type hints
        """Inspects subclasses to ensure all methods are static."""
        super().__init_subclass__(**kwargs)
        for name, value in vars(cls).items():
            if name.startswith("__"):
                continue
            # Ensure that any callable attribute is a staticmethod instance
            if callable(value) and not isinstance(value, staticmethod):
                raise TypeError(
                    f"Ruleset class '{cls.__name__}' has a non-static method '{name}'. "
                    f"All methods in a Ruleset must be decorated with @staticmethod."
                )


class StatefulEntity:
    """A base class that ENFORCES the stateful shell pattern."""

    _rules: type | None = None  # Class-level rules provider
    _instance_rules: Ruleset | None = None  # Instance-level rules provider

    def __init__(
        self,
        initial_state: dict[str, Any] | None = None,
        ruleset_instance: Ruleset | None = None,
    ):
        """
        Initializes the StatefulEntity.

        Args:
            initial_state: An optional dictionary to initialize instance attributes.
                           Keys should correspond to attribute names.
            ruleset_instance: An optional Ruleset instance to override class-level
                              rules.
        """
        if initial_state:
            for key, value in initial_state.items():
                setattr(self, key, value)

        if ruleset_instance:
            self._instance_rules = ruleset_instance
        elif not hasattr(self, "_instance_rules"):  # Ensure _instance_rules exists
            self._instance_rules = None

    def __init_subclass__(cls, **kwargs: Any) -> None:  # Added type hints
        """Enforces that no methods in subclasses are actual implementations."""
        super().__init_subclass__(**kwargs)
        for name, value in vars(cls).items():
            if name.startswith("__") or name in ("_rules", "_instance_rules"):
                continue  # Skip dunder methods, _rules, and _instance_rules

            # Check if it's a PureShellMethod (already processed)
            if isinstance(value, PureShellMethod):
                continue

            # Check if it's tagged as a side_effect_method
            if hasattr(value, "_is_side_effect") and getattr(value, "_is_side_effect"):
                continue

            # Check if it's a property
            if isinstance(value, property):
                # You might want to inspect fget, fset, fdel of the property
                # For now, we'll assume properties are fine or handled elsewhere
                continue

            if callable(value):
                raise TypeError(
                    f"Class '{cls.__name__}' has an implemented method '{name}'. "
                    f"Methods in StatefulEntity subclasses must be decorated with "
                    f"@shell_method or @side_effect_method, or be properties."
                )


__version__ = "0.2.0"

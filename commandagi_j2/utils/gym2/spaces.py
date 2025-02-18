from abc import ABC, abstractmethod
from typing import (
    Type,
    Any,
    List,
    Dict,
    Literal,
    Optional,
    Set,
    Union,
    get_type_hints,
    get_origin,
    get_args,
    Generic,
    TypeVar,
)
from pydantic import ValidationError, BaseModel, Field
from random import choice, randint, uniform
import string
from enum import Enum
import types  # for types.UnionType

# Define generic type variables for spaces.
T = TypeVar("T")  # Base type for a given space
E = TypeVar("E")  # Element type (e.g. for ListSpace)
K = TypeVar("K")  # Key type for dictionaries (e.g. in DictSpace)
V = TypeVar("V")  # Value type for dictionaries (e.g. in DictSpace)
SM = TypeVar("SM", bound=BaseModel)  # For StructuredSpace models


class Space(BaseModel, ABC, Generic[T]):
    """
    Abstract base class for observation and action spaces.

    The generic parameter (T) is optional: you can use a Space without specifying a type,
    though specifying it adds extra type safety when you use your spaces.
    """

    @abstractmethod
    def contains(self, x: T) -> bool:
        """Check if x is a valid member of this space."""

    @abstractmethod
    def sample(self) -> T:
        """Randomly sample a valid value from this space."""


class DiscreteSpace(Space[T], Generic[T]):
    """Space with a finite set of possible values.

    >>> space = DiscreteSpace(values=[1, 2, 3])
    >>> space.contains(2)
    True
    >>> space.contains(4)
    False
    >>> sample = space.sample()
    >>> sample in [1, 2, 3]
    True
    """

    values: List[T]

    def contains(self, x: T) -> bool:
        return x in self.values

    def sample(self) -> T:
        return choice(self.values)


class SingletonSpace(Space[T], Generic[T]):
    """Space containing exactly one value.

    >>> space = SingletonSpace(value=42)
    >>> space.contains(42)
    True
    >>> space.contains(43)
    False
    >>> space.sample()
    42
    """

    value: T

    def contains(self, x: T) -> bool:
        return x == self.value

    def sample(self) -> T:
        return self.value


class IntegerSpace(Space[int]):
    """Space for integer values with optional bounds.

    You can simply use IntegerSpace() without specifying the type parameter.

    >>> space = IntegerSpace(min_value=0, max_value=10)
    >>> space.contains(5)
    True
    >>> space.contains(-1)
    False
    >>> sample = space.sample()
    >>> 0 <= sample <= 10
    True
    >>> isinstance(sample, int)
    True
    """

    min_value: Optional[int] = None
    max_value: Optional[int] = None
    sample_default_min: int = -100  # Default min when no bounds provided
    sample_default_max: int = 100  # Default max when no bounds provided

    def contains(self, x: int) -> bool:
        if not isinstance(x, int):
            return False
        if self.min_value is not None and x < self.min_value:
            return False
        if self.max_value is not None and x > self.max_value:
            return False
        return True

    def sample(self) -> int:
        min_val = (
            self.min_value if self.min_value is not None else self.sample_default_min
        )
        max_val = (
            self.max_value if self.max_value is not None else self.sample_default_max
        )
        return randint(min_val, max_val)


class FloatSpace(Space[float]):
    """Space for float values with optional bounds.

    >>> space = FloatSpace(min_value=0.0, max_value=1.0)
    >>> space.contains(0.5)
    True
    >>> space.contains(-0.1)
    False
    >>> sample = space.sample()
    >>> 0.0 <= sample <= 1.0
    True
    """

    min_value: Optional[float] = None
    max_value: Optional[float] = None
    sample_default_min: float = -100.0  # Default min when no bounds provided
    sample_default_max: float = 100.0  # Default max when no bounds provided

    def contains(self, x: float) -> bool:
        if not isinstance(x, (int, float)):  # Allow integers as valid floats
            return False
        if self.min_value is not None and x < self.min_value:
            return False
        if self.max_value is not None and x > self.max_value:
            return False
        return True

    def sample(self) -> float:
        min_val = (
            self.min_value if self.min_value is not None else self.sample_default_min
        )
        max_val = (
            self.max_value if self.max_value is not None else self.sample_default_max
        )
        return uniform(min_val, max_val)


class BooleanSpace(Space[bool]):
    """Space for boolean values.

    >>> space = BooleanSpace()
    >>> space.contains(True)
    True
    >>> space.contains(False)
    True
    >>> isinstance(space.sample(), bool)
    True
    """

    def contains(self, x: bool) -> bool:
        return isinstance(x, bool)

    def sample(self) -> bool:
        return choice([True, False])


class StringSpace(Space[str]):
    """Space for string values with optional constraints.

    >>> space = StringSpace(min_length=2, max_length=4, allowed_chars=set('abc'))
    >>> space.contains('abc')
    True
    >>> space.contains('a')
    False
    >>> sample = space.sample()
    >>> 2 <= len(sample) <= 4
    True
    """

    min_length: Optional[int] = None
    max_length: Optional[int] = None
    allowed_chars: Set[str] = Field(default_factory=lambda: set(string.printable))
    sample_default_min_length: int = 0
    sample_default_max_length: int = 10

    def contains(self, x: str) -> bool:
        if not isinstance(x, str):
            return False
        if self.min_length is not None and len(x) < self.min_length:
            return False
        if self.max_length is not None and len(x) > self.max_length:
            return False
        return all(c in self.allowed_chars for c in x)

    def sample(self) -> str:
        min_len = (
            self.min_length
            if self.min_length is not None
            else self.sample_default_min_length
        )
        max_len = (
            self.max_length
            if self.max_length is not None
            else self.sample_default_max_length
        )
        length = randint(min_len, max_len)
        chars = list(self.allowed_chars)
        return "".join(choice(chars) for _ in range(length))


class DictSpace(Space[Dict[K, V]], Generic[K, V]):
    """Space for dictionary values with specified subspaces for each key.

    The generic types for keys and values are optional, but used here for added type safety.

    >>> from enum import Enum
    >>> class MouseButton(Enum):
    ...     LEFT = "left"
    ...     RIGHT = "right"
    >>> bool_space = BooleanSpace()
    >>> space = DictSpace(spaces={button: bool_space for button in MouseButton})
    >>> sample = space.sample()
    >>> all(isinstance(k, MouseButton) and isinstance(v, bool) for k, v in sample.items())
    True
    """

    spaces: Dict[K, Space[V]]

    def contains(self, x: Dict[Any, Any]) -> bool:
        if not isinstance(x, dict):
            return False
        if set(x.keys()) != set(self.spaces.keys()):
            return False
        return all(space.contains(x[key]) for key, space in self.spaces.items())

    def sample(self) -> Dict[K, V]:
        return {key: space.sample() for key, space in self.spaces.items()}


class TupleSpace(Space[tuple]):
    """Space for fixed-length tuples with heterogeneous subspaces.

    >>> subspaces = [IntegerSpace(min_value=0, max_value=10),
    ...              IntegerSpace(min_value=0, max_value=10)]
    >>> space = TupleSpace(subspaces=subspaces)
    >>> x = space.sample()
    >>> isinstance(x, tuple) and len(x) == 2
    True
    """

    subspaces: List[Space[Any]]

    def contains(self, x: Any) -> bool:
        if not isinstance(x, tuple):
            return False
        if len(x) != len(self.subspaces):
            return False
        return all(space.contains(item) for space, item in zip(self.subspaces, x))

    def sample(self) -> tuple:
        return tuple(space.sample() for space in self.subspaces)


class ListSpace(Space[List[E]], Generic[E]):
    """Space for list values with a specified subspace for elements.

    The generic type for the element is optional; use this if you want extra type hints.

    >>> int_space = IntegerSpace(min_value=0, max_value=10)
    >>> space = ListSpace(subspace=int_space, min_length=2, max_length=4)
    >>> space.contains([1, 2, 3])
    True
    """

    subspace: Space[E]
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    sample_default_min_length: int = 0
    sample_default_max_length: int = 10

    def contains(self, x: List[E]) -> bool:
        if not isinstance(x, list):
            return False
        if self.min_length is not None and len(x) < self.min_length:
            return False
        if self.max_length is not None and len(x) > self.max_length:
            return False
        return all(self.subspace.contains(item) for item in x)

    def sample(self) -> List[E]:
        min_len = (
            self.min_length
            if self.min_length is not None
            else self.sample_default_min_length
        )
        max_len = (
            self.max_length
            if self.max_length is not None
            else self.sample_default_max_length
        )
        length = randint(min_len, max_len)
        return [self.subspace.sample() for _ in range(length)]


class SetSpace(Space[Set[E]], Generic[E]):
    """Space for set values with a specified subspace for elements.

    The generic type for the element is optional; use this if you want extra type hints.

    >>> int_space = IntegerSpace(min_value=0, max_value=10)
    >>> space = SetSpace(subspace=int_space, min_length=2, max_length=4)
    >>> space.contains({1, 2, 3})
    True
    """

    subspace: Space[E]
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    sample_default_min_length: int = 0
    sample_default_max_length: int = 10

    def contains(self, x: Set[E]) -> bool:
        if not isinstance(x, set):
            return False
        if self.min_length is not None and len(x) < self.min_length:
            return False
        if self.max_length is not None and len(x) > self.max_length:
            return False
        return all(self.subspace.contains(item) for item in x)

    def sample(self) -> Set[E]:
        min_len = (
            self.min_length
            if self.min_length is not None
            else self.sample_default_min_length
        )
        max_len = (
            self.max_length
            if self.max_length is not None
            else self.sample_default_max_length
        )
        length = randint(min_len, max_len)
        return set(self.subspace.sample() for _ in range(length))


class UnionSpace(Space[T], Generic[T]):
    """Space that accepts values from any of its component spaces.

    >>> int_space = IntegerSpace(min_value=0, max_value=10)
    >>> str_space = StringSpace(allowed_chars=set('abc'))
    >>> space = UnionSpace(spaces=[int_space, str_space])
    >>> space.contains(5)
    True
    """

    spaces: List[Space[T]]

    def contains(self, x: T) -> bool:
        return any(space.contains(x) for space in self.spaces)

    def sample(self) -> T:
        return choice(self.spaces).sample()


class StructuredSpace(Space[SM], Generic[SM]):
    """Space for validating and sampling Pydantic model instances.

    The model's type is specified by the generic, which is optional. If not supplied,
    you can still instantiate StructuredSpace with the model keyword argument.

    >>> from pydantic import BaseModel
    >>> class Point(BaseModel):
    ...     x: int
    ...     y: int
    >>> space = StructuredSpace(model=Point)
    >>> space.contains(Point(x=1, y=2))
    True
    """

    model: Type[SM]
    _field_spaces: Dict[str, Space[Any]] = {}

    def __init__(self, **data):
        super().__init__(**data)
        self._field_spaces = {}
        self._analyze_model_fields()

    def _analyze_model_fields(self):
        """Recursively analyze model fields and create appropriate spaces."""
        type_hints = get_type_hints(self.model)
        for field_name, field_type in type_hints.items():
            if field_name.startswith("_"):
                continue
            if hasattr(field_type, "__metadata__"):
                # Field already has a space annotation
                self._field_spaces[field_name] = field_type.__metadata__[0]
            else:
                self._field_spaces[field_name] = self._create_space_for_type(field_type)

    def _normalize_type(self, type_: Any) -> tuple:
        """
        Convert a type annotation into a structured tuple representation for easier processing.
        The tuple's first element indicates the kind:
          - ("optional", inner_type) for Optional types
          - ("union", (arg1, arg2, ...)) for unions
          - ("list", element_type) for list[...] types
          - ("tuple", (elem1, elem2, ...)) for fixed-length tuples
          - ("var_tuple", element_type) for variable-length tuples (using Ellipsis) [not supported]
          - ("dict", key_type, value_type) for dict[...] types
          - ("literal", [literal1, literal2, ...]) for Literals
          - ("scalar", type) for all other types
        """
        origin = get_origin(type_)
        if origin in (Union, types.UnionType):
            args = get_args(type_)
            if len(args) == 2 and type(None) in args:
                non_none_type = next(t for t in args if t is not type(None))
                return ("optional", non_none_type)
            return ("union", args)
        elif origin is set:
            (elt,) = get_args(type_)
            return ("set", elt)
        elif origin is list:
            (elt,) = get_args(type_)
            return ("list", elt)
        elif origin is tuple:
            args = get_args(type_)
            if len(args) == 2 and args[1] is Ellipsis:
                return ("var_tuple", args[0])
            return ("tuple", args)
        elif origin is dict:
            key_type, value_type = get_args(type_)
            return ("dict", key_type, value_type)
        elif origin is Literal:
            return ("literal", list(get_args(type_)))
        else:
            return ("scalar", type_)

    def _create_space_for_type(self, type_: Any) -> Space[Any]:
        """
        Create an appropriate space for a given type using its normalized representation.
        Supports Optional, Union, List, Tuple, Dict, Literals, nested Pydantic models, and basic types.
        """
        normalized = self._normalize_type(type_)
        kind = normalized[0]

        if kind == "optional":
            inner_type = normalized[1]
            inner_space = self._create_space_for_type(inner_type)
            singleton_space = SingletonSpace(value=None)
            return UnionSpace(spaces=[inner_space, singleton_space])
        elif kind == "union":
            args = normalized[1]
            return UnionSpace(spaces=[self._create_space_for_type(t) for t in args])
        elif kind == "set":
            element_type = normalized[1]
            return SetSpace(subspace=self._create_space_for_type(element_type))
        elif kind == "list":
            element_type = normalized[1]
            return ListSpace(subspace=self._create_space_for_type(element_type))
        elif kind == "tuple":
            subspaces = [self._create_space_for_type(t) for t in normalized[1]]
            return TupleSpace(subspaces=subspaces)
        elif kind == "var_tuple":
            raise ValueError("Variable-length tuples are not supported.")
        elif kind == "dict":
            key_type, value_type = normalized[1], normalized[2]
            if key_type is str:
                return DictSpace[str, Any](spaces={})
            elif isinstance(key_type, type) and issubclass(key_type, Enum):
                keys = list(key_type)
                spaces_dict = {
                    key: self._create_space_for_type(value_type) for key in keys
                }
                return DictSpace[str, Any](spaces=spaces_dict)
            else:
                raise ValueError(f"Dict keys must be strings or Enum, got {key_type}")
        elif kind == "literal":
            return DiscreteSpace[Any](values=normalized[1])
        elif kind == "scalar":
            base = normalized[1]
            if isinstance(base, type) and issubclass(base, BaseModel):
                return StructuredSpace[Any](model=base)
            if isinstance(base, type) and issubclass(base, Enum):
                return DiscreteSpace[Any](values=list(base))
            if base is str:
                return StringSpace()
            if base is int:
                return IntegerSpace()
            if base is float:
                return FloatSpace()
            if base is bool:
                return BooleanSpace()
            raise ValueError(f"Unsupported type: {base}")
        else:
            raise ValueError(f"Unsupported type kind: {kind}")

    def contains(self, x: SM) -> bool:
        if not isinstance(x, self.model):
            return False
        for field_name, space in self._field_spaces.items():
            value = getattr(x, field_name)
            if not space.contains(value):
                return False
        return True

    def sample(self) -> SM:
        sample_data = {
            field_name: space.sample()
            for field_name, space in self._field_spaces.items()
        }
        return self.model(**sample_data)

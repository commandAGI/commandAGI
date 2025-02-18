from abc import ABC, abstractmethod
from typing import Any, List, Dict, Literal, Optional, Set, Union, Annotated
from typing_extensions import get_type_hints, get_origin, get_args
from pydantic import ValidationError, BaseModel, Field
from random import choice, randint, uniform
import string
from enum import Enum
import types  # for types.UnionType


class Space(BaseModel, ABC):
    """
    Abstract base class for observation and action spaces.
    """

    @abstractmethod
    def contains(self, x: Any) -> bool:
        """Check if x is a valid member of this space."""

    @abstractmethod
    def sample(self) -> Any:
        """Randomly sample a valid value from this space."""


class DiscreteSpace(Space):
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

    values: List[Any]

    def contains(self, x: Any) -> bool:
        return x in self.values

    def sample(self) -> Any:
        return choice(self.values)


class SingletonSpace(Space):
    """Space containing exactly one value.

    >>> space = SingletonSpace(value=42)
    >>> space.contains(42)
    True
    >>> space.contains(43)
    False
    >>> space.sample()
    42
    """

    value: Any

    def contains(self, x: Any) -> bool:
        return x == self.value

    def sample(self) -> Any:
        return self.value


class IntegerSpace(Space):
    """Space for integer values with optional bounds.

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


class FloatSpace(Space):
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


class BooleanSpace(Space):
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


class StringSpace(Space):
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


class DictSpace(Space):
    """Space for dictionary values with specified subspaces for each key.

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

    spaces: Dict[Any, Space]

    def contains(self, x: Dict[Any, Any]) -> bool:
        if not isinstance(x, dict):
            return False
        if set(x.keys()) != set(self.spaces.keys()):
            return False
        return all(space.contains(x[key]) for key, space in self.spaces.items())

    def sample(self) -> Dict[Any, Any]:
        return {key: space.sample() for key, space in self.spaces.items()}


class TupleSpace(Space):
    """Space for fixed-length tuples with heterogeneous subspaces.

    >>> subspaces = [IntegerSpace(min_value=0, max_value=10),
    ...              IntegerSpace(min_value=0, max_value=10)]
    >>> space = TupleSpace(subspaces=subspaces)
    >>> x = space.sample()
    >>> isinstance(x, tuple) and len(x) == 2
    True
    """

    subspaces: List[Space]

    def contains(self, x: Any) -> bool:
        if not isinstance(x, tuple):
            return False
        if len(x) != len(self.subspaces):
            return False
        return all(space.contains(item) for space, item in zip(self.subspaces, x))

    def sample(self) -> tuple:
        return tuple(space.sample() for space in self.subspaces)


class ListSpace(Space):
    """Space for list values with a specified subspace for elements.

    >>> int_space = IntegerSpace(min_value=0, max_value=10)
    >>> space = ListSpace(subspace=int_space, min_length=2, max_length=4)
    >>> space.contains([1, 2, 3])
    True
    """

    subspace: Space
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    sample_default_min_length: int = 0
    sample_default_max_length: int = 10

    def contains(self, x: List[Any]) -> bool:
        if not isinstance(x, list):
            return False
        if self.min_length is not None and len(x) < self.min_length:
            return False
        if self.max_length is not None and len(x) > self.max_length:
            return False
        return all(self.subspace.contains(item) for item in x)

    def sample(self) -> List[Any]:
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


class SetSpace(Space):
    """Space for set values with a specified subspace for elements.

    >>> int_space = IntegerSpace(min_value=0, max_value=10)
    >>> space = SetSpace(subspace=int_space, min_length=2, max_length=4)
    >>> space.contains({1, 2, 3})
    True
    """

    subspace: Space
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    sample_default_min_length: int = 0
    sample_default_max_length: int = 10

    def contains(self, x: Set[Any]) -> bool:
        if not isinstance(x, set):
            return False
        if self.min_length is not None and len(x) < self.min_length:
            return False
        if self.max_length is not None and len(x) > self.max_length:
            return False
        return all(self.subspace.contains(item) for item in x)

    def sample(self) -> Set[Any]:
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


class UnionSpace(Space):
    """Space that accepts values from any of its component spaces.

    >>> int_space = IntegerSpace(min_value=0, max_value=10)
    >>> str_space = StringSpace(allowed_chars=set('abc'))
    >>> space = UnionSpace(spaces=[int_space, str_space])
    >>> space.contains(5)
    True
    """

    spaces: List[Space]

    def contains(self, x: Any) -> bool:
        return any(space.contains(x) for space in self.spaces)

    def sample(self) -> Any:
        return choice(self.spaces).sample()


class StructuredSpace(Space):
    """Space for validating and sampling Pydantic model instances.

    >>> from pydantic import BaseModel
    >>> class Point(BaseModel):
    ...     x: int
    ...     y: int
    >>> space = StructuredSpace(model=Point)
    >>> space.contains(Point(x=1, y=2))
    True
    """

    model: type
    _field_spaces: Dict[str, Space] = {}

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
            if get_origin(field_type) is Annotated:
                # Field already has a space annotation as metadata
                _, *metadata = get_args(field_type)
                self._field_spaces[field_name] = metadata[0]
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

    def _create_space_for_type(self, type_: Any) -> Space:
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
                return DictSpace(spaces={})
            elif isinstance(key_type, type) and issubclass(key_type, Enum):
                keys = list(key_type)
                spaces_dict = {
                    key: self._create_space_for_type(value_type) for key in keys
                }
                return DictSpace(spaces=spaces_dict)
            else:
                raise ValueError(f"Dict keys must be strings or Enum, got {key_type}")
        elif kind == "literal":
            return DiscreteSpace(values=normalized[1])
        elif kind == "scalar":
            base = normalized[1]
            if isinstance(base, type) and issubclass(base, BaseModel):
                return StructuredSpace(model=base)
            if isinstance(base, type) and issubclass(base, Enum):
                return DiscreteSpace(values=list(base))
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

    def contains(self, x: Any) -> bool:
        if not isinstance(x, self.model):
            return False
        for field_name, space in self._field_spaces.items():
            value = getattr(x, field_name)
            if not space.contains(value):
                return False
        return True

    def sample(self) -> Any:
        sample_data = {
            field_name: space.sample()
            for field_name, space in self._field_spaces.items()
        }
        return self.model(**sample_data)

from abc import ABC, abstractmethod
from typing import Type
from pydantic import ValidationError
from random import choice, randint
import string
from typing import List, Dict, Any, Literal, Optional, Set
from pydantic import BaseModel, Field


class Space(BaseModel, ABC):
    """Abstract base class for observation and action spaces."""

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
    >>> space.contains(11)
    False
    >>> space.contains(3.14)
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

    def contains(self, x: Any) -> bool:
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
    >>> space.contains(1.1)
    False
    >>> space.contains("0.5")
    False
    >>> sample = space.sample()
    >>> 0.0 <= sample <= 1.0
    True
    >>> isinstance(sample, float)
    True
    """

    min_value: Optional[float] = None
    max_value: Optional[float] = None
    sample_default_min: float = -100.0  # Default min when no bounds provided
    sample_default_max: float = 100.0  # Default max when no bounds provided

    def contains(self, x: Any) -> bool:
        if not isinstance(x, (int, float)):  # Allow integers as valid floats
            return False
        if self.min_value is not None and x < self.min_value:
            return False
        if self.max_value is not None and x > self.max_value:
            return False
        return True

    def sample(self) -> float:
        from random import uniform

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
    False
    >>> space.contains(1)
    False
    >>> isinstance(space.sample(), bool)
    True
    """

    def contains(self, x: Any) -> bool:
        return isinstance(x, bool)

    def sample(self) -> bool:
        from random import choice

        return choice([True, False])


class StringSpace(Space):
    """Space for string values with optional constraints.

    >>> space = StringSpace(min_length=2, max_length=4, allowed_chars=set('abc'))
    >>> space.contains('abc')
    True
    >>> space.contains('a')
    False
    >>> space.contains('abcde')
    False
    >>> space.contains('def')
    False
    >>> sample = space.sample()
    >>> 2 <= len(sample) <= 4
    True
    >>> all(c in 'abc' for c in sample)
    True
    """

    min_length: Optional[int] = None
    max_length: Optional[int] = None
    allowed_chars: Set[str] = Field(default_factory=lambda: set(string.printable))
    sample_default_min_length: int = 0  # Default min length when no bounds provided
    sample_default_max_length: int = 10  # Default max length when no bounds provided

    def contains(self, x: str) -> bool:
        if not isinstance(x, str):
            return False

        if self.min_length is not None and len(x) < self.min_length:
            return False

        if self.max_length is not None and len(x) > self.max_length:
            return False

        return all(c in self.allowed_chars for c in x)

    def sample(self) -> str:
        min_len = self.min_length or self.sample_default_min_length
        max_len = self.max_length or self.sample_default_max_length
        length = randint(min_len, max_len)

        chars = list(self.allowed_chars)
        return "".join(choice(chars) for _ in range(length))


class DictSpace(Space):
    """Space for dictionary values with specified subspaces for each key.

    >>> int_space = IntegerSpace(min_value=0, max_value=10)
    >>> space = DictSpace(spaces={'a': int_space, 'b': int_space})
    >>> space.contains({'a': 5, 'b': 7})
    True
    >>> space.contains({'a': 5})
    False
    >>> space.contains({'a': -1, 'b': 7})
    False
    >>> sample = space.sample()
    >>> isinstance(sample, dict)
    True
    >>> all(0 <= v <= 10 for v in sample.values())
    True
    """

    spaces: Dict[str, Space]

    def contains(self, x: Dict[str, Any]) -> bool:
        if not isinstance(x, dict):
            return False

        if set(x.keys()) != set(self.spaces.keys()):
            return False

        return all(space.contains(x[key]) for key, space in self.spaces.items())

    def sample(self) -> Dict[str, Any]:
        return {key: space.sample() for key, space in self.spaces.items()}


class ListSpace(Space):
    """Space for list values with a specified subspace for elements.

    >>> int_space = IntegerSpace(min_value=0, max_value=10)
    >>> space = ListSpace(subspace=int_space, min_length=2, max_length=4)
    >>> space.contains([1, 2, 3])
    True
    >>> space.contains([1])
    False
    >>> space.contains([1, 2, 3, 4, 5])
    False
    >>> space.contains([1, -1, 3])
    False
    >>> sample = space.sample()
    >>> 2 <= len(sample) <= 4
    True
    >>> all(0 <= x <= 10 for x in sample)
    True
    """

    subspace: Space
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    sample_default_min_length: int = 0  # Default min length when no bounds provided
    sample_default_max_length: int = 10  # Default max length when no bounds provided

    def contains(self, x: List[Any]) -> bool:
        if not isinstance(x, list):
            return False

        if self.min_length is not None and len(x) < self.min_length:
            return False

        if self.max_length is not None and len(x) > self.max_length:
            return False

        return all(self.subspace.contains(item) for item in x)

    def sample(self) -> List[Any]:
        min = self.min_length or self.sample_default_min_length
        max = self.max_length or self.sample_default_max_length
        length = randint(min, max)
        return [self.subspace.sample() for _ in range(length)]


class UnionSpace(Space):
    """Space that accepts values from any of its component spaces.

    >>> int_space = IntegerSpace(min_value=0, max_value=10)
    >>> str_space = StringSpace(allowed_chars=set('abc'))
    >>> space = UnionSpace(spaces=[int_space, str_space])
    >>> space.contains(5)
    True
    >>> space.contains('abc')
    True
    >>> space.contains(-1)
    False
    >>> space.contains('def')
    False
    >>> sample = space.sample()
    >>> isinstance(sample, (int, str))
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
    >>> space.contains(Point(x='1', y=2))
    False
    >>> sample = space.sample()
    >>> isinstance(sample, Point)
    True
    """

    model: Type[BaseModel]
    _field_spaces: Dict[str, Space]

    def __init__(self, model: Type[BaseModel]):
        self.model = model
        self._field_spaces = {}
        self._analyze_model_fields()

    def _analyze_model_fields(self):
        """Recursively analyze model fields and create appropriate spaces."""
        for field_name, field in self.model.model_fields.items():
            if field_name.startswith("_"):
                continue

            if hasattr(field.type_, "__metadata__"):
                # Field already has space annotation
                self._field_spaces[field_name] = field.type_.__metadata__[0]
            else:
                # Create appropriate space based on field type
                self._field_spaces[field_name] = self._create_space_for_type(
                    field.type_
                )

    def _create_space_for_type(self, type_: Any) -> Space:
        """Create appropriate space for a given type."""
        # Handle Lists
        if hasattr(type_, "__origin__") and type_.__origin__ is list:
            element_type = type_.__args__[0]
            return ListSpace(subspace=self._create_space_for_type(element_type))

        # Handle Dicts
        if hasattr(type_, "__origin__") and type_.__origin__ is dict:
            key_type, value_type = type_.__args__
            if key_type is str:  # Only support str keys for now
                return DictSpace({}, self._create_space_for_type(value_type))
            raise ValueError(f"Dict keys must be strings, got {key_type}")

        # Handle Literals
        if hasattr(type_, "__origin__") and type_.__origin__ is Literal:
            return UnionSpace([SingletonSpace(val) for val in type_.__args__])

        # Handle nested BaseModels
        if isinstance(type_, type) and issubclass(type_, BaseModel):
            return StructuredSpace(model=type_)

        # Handle basic types
        if type_ is str:
            return StringSpace()
        if type_ is int:
            return IntegerSpace()
        if type_ is float:
            return FloatSpace()
        if type_ is bool:
            return BooleanSpace()

        raise ValueError(f"Unsupported type: {type_}")

    def contains(self, x: Any) -> bool:
        if not isinstance(x, self.model):
            return False
        try:
            self.model.validate(x)
            return all(
                space.contains(getattr(x, field_name))
                for field_name, space in self._field_spaces.items()
            )
        except ValidationError:
            return False

    def sample(self) -> BaseModel:
        sample_data = {
            field_name: space.sample()
            for field_name, space in self._field_spaces.items()
        }
        return self.model(**sample_data)

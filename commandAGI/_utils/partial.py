from typing import TypeVar, Dict, Any, Type

T = TypeVar("T")


class Partial(Dict[str, Any]):
    """A type hint for partial updates to a model.

    Example:
        partial_update: Partial[User] = {"name": "New Name"}
    """

    def __class_getitem__(cls, item: Type[T]) -> Type[Dict[str, Any]]:
        return Dict[str, Any]

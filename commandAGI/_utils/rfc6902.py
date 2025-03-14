from typing import TypeVar, Generic, Literal, Union
from pydantic import Field, BaseModel

T = TypeVar("T")


# Standard JSON Patch operations (RFC 6902)
class BasePatchOperation(BaseModel, Generic[T]):
    path: str


class AddOperation(BasePatchOperation[T]):
    op: Literal["add"]
    value: T


class RemoveOperation(BasePatchOperation[T]):
    op: Literal["remove"]


class ReplaceOperation(BasePatchOperation[T]):
    op: Literal["replace"]
    value: T


class MoveOperation(BasePatchOperation[T]):
    op: Literal["move"]
    from_: str = Field(..., alias="from")


class CopyOperation(BasePatchOperation[T]):
    op: Literal["copy"]
    from_: str = Field(..., alias="from")


class TestOperation(BasePatchOperation[T]):
    op: Literal["test"]
    value: T


# RFC 6902 compliant union type
JsonPatchOperation = Union[
    AddOperation[T],
    RemoveOperation[T],
    ReplaceOperation[T],
    MoveOperation[T],
    CopyOperation[T],
    TestOperation[T],
]
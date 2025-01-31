from abc import abstractmethod
from typing import (
    Optional,
    List,
    TypeVar,
    Type,
    Dict,
    Any,
    Generic,
    cast,
)

from pydantic.main import BaseModel

from beanie.sync.odm.interfaces.run import RunInterface
from beanie.sync.odm.utils.parsing import parse_obj

CursorResultType = TypeVar("CursorResultType")


class BaseCursorQuery(Generic[CursorResultType], RunInterface):
    """
    BaseCursorQuery class. Wrapper over AsyncIOMotorCursor,
    which parse result with model
    """

    cursor = None

    @abstractmethod
    def get_projection_model(self) -> Optional[Type[BaseModel]]:
        ...

    @property
    @abstractmethod
    def motor_cursor(self):
        ...

    def _cursor_params(self):
        ...

    def __iter__(self):
        if self.cursor is None:
            self.cursor = self.motor_cursor
        return self

    def __next__(self) -> CursorResultType:
        if self.cursor is None:
            raise RuntimeError("cursor was not set")
        next_item = self.cursor.__next__()
        projection = self.get_projection_model()
        if projection is None:
            return next_item
        return parse_obj(projection, next_item)  # type: ignore

    def _get_cache(self) -> List[Dict[str, Any]]:
        ...

    def _set_cache(self, data):
        ...

    def to_list(
        self, length: Optional[int] = None
    ) -> List[CursorResultType]:  # noqa
        """
        Get list of documents

        :param length: Optional[int] - length of the list
        :return: Union[List[BaseModel], List[Dict[str, Any]]]
        """
        cursor = self.motor_cursor
        if cursor is None:
            raise RuntimeError("self.motor_cursor was not set")
        motor_list: List[Dict[str, Any]] = self._get_cache()
        if motor_list is None:
            motor_list = list(cursor)[:length]
            self._set_cache(motor_list)
        projection = self.get_projection_model()
        if projection is not None:
            return cast(
                List[CursorResultType],
                [parse_obj(projection, i) for i in motor_list],
            )
        return cast(List[CursorResultType], motor_list)

    def run(self):
        return self.to_list()

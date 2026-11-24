from enum import Enum


class DanglingEdges(str, Enum):
    FORBID = "forbid"
    DELETE = "delete"


class SelectionStrategy(Enum):
    ALL_ASCENDING = 1
    FIRST_LOWEST = 2


class DanglingEdgesHandling(Enum):
    CANCEL = 1
    DELETE = 2

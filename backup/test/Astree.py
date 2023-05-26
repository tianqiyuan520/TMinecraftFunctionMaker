from enum import Enum,auto

class NodeType(Enum):
    ##节点
    PROGRAM = auto()
    STMT = auto()


class Program:
    def __init__(self) -> None:
        self.type:NodeType=NodeType.PROGRAM
        self.body:list[Stmt] = []

class Stmt:
    def __init__(self) -> None:
        self.type:NodeType=NodeType.STMT
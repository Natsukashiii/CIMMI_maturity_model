from enum import Enum
from typing import List


class Level(Enum):
    NONE = 0
    BASIC = 1
    INTERMEDIATE = 2
    ADVANCED = 3


class Todo:
    def __init__(self, level, frequency, task):
        self.frequency = frequency
        self.level = level
        self.task = task

    def __lt__(self, other):
        if self.level.value < other.level.value:
            return True
        if self.level.value == other.level.value:
            return self.frequency > other.frequency
        return False


class Task:
    def __init__(self, name: str, instances: list, level: str, frequency: int):
        self.instances = instances
        self.count = 0
        self.name = name
        self.frequency = frequency
        match level:
            case "basic":
                self.level = Level.BASIC
            case "intermediate":
                self.level = Level.INTERMEDIATE
            case "advanced":
                self.level = Level.ADVANCED

    def __iadd__(self, other):
        self.count += other
        return self

    def __str__(self):
        return f"{self.name} [{self.count}]"

    def str(self, total):
        return f" - {self.name} [{self.count}/{total}]"

    def __gt__(self, other):
        return self.count > other.count

    def __trunc__(self):
        return self.name[10:]


class AutomationSubdomain:
    def __init__(self, name: str, child: List[Task] = None):
        self.child = child or []
        self.name = name
        self.count = 0
        self.description = ""

    def __str__(self):
        return self.name

    def str(self, total):
        if self.count == 0:
            return f"\n{self}"
        return f"\n{self} [{self.count}/{total}]"

    def __iadd__(self, other):
        self.count += other
        return self

    def __gt__(self, other):
        return self.count > other.count


class AutomationDomain:
    def __init__(self, name: str, child: List[AutomationSubdomain] = None):
        self.child = child or []
        self.name = name
        self.count = 0

    def __str__(self):
        return self.name

    def str(self, total):
        if self.count == 0:
            return f"\n{self}"
        return f"\n{self} [{self.count}/{total}]"

    def __iadd__(self, other):
        self.count += other
        return self

    def __gt__(self, other):
        return self.count > other.count

from typing import Callable

from yazelc.cutscene.task import Task
from yazelc.zesper import World


class FunctionTask(Task):
    """ Calls a function at a later stage"""

    def __init__(self, function: Callable[[], None], number_of_calls: int = 0):
        # NOTE: The objects referenced in this function could be "dead" at the time it is called or
        # conversely, they may be not released until the instance is garbage collected
        self.function = function
        self.number_of_calls = number_of_calls
        self.counter = 0
        self.finished = False

    def update(self, world: World):
        self.function()
        self.counter += 1
        if self.counter == self.number_of_calls:
            self.finished = True

    def is_finished(self, world: World) -> bool:
        return self.finished

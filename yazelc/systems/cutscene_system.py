import logging
from collections import deque
from typing import Generator

from yazelc import zesper
from yazelc.cutscene.task import Task

logger = logging.getLogger(__name__)


class CutsceneSystem(zesper.Processor):
    """
    Runs list of Task types which are coroutines (generators) as a cutscene.
    It is possible to run in parallel more than one list of tasks.
    """

    def __init__(self, world: zesper.World, *all_task_lists: list[Task]):
        super().__init__()
        self.world = world

        self.coroutine_list = dict()
        for task_list in all_task_lists:
            self.add_task_list(task_list)

    def process(self, *args, **kwargs):
        task_list_to_remove = []

        for id_, coroutine in self.coroutine_list.items():
            try:
                next(coroutine)
            except StopIteration:
                task_list_to_remove.append(id_)
                logger.debug(f'Finished task list {coroutine}')

        for task_list_id in task_list_to_remove:
            self.coroutine_list.pop(task_list_id)

    def add_task_list(self, task_list):
        coroutine = self._get_coroutine(task_list)
        self.coroutine_list.update({hex(id(coroutine)): coroutine})
        logger.debug(f'Adding task list: {str(coroutine)}')

    def _get_coroutine(self, task_list: list[Task]) -> Generator:
        # TODO: Check the example of cycle in itertools to see how can we have infinite cycle for a task list
        task_queue = deque(task_list)
        while task_queue:
            task = task_queue.popleft()
            yield from task.run(self.world)

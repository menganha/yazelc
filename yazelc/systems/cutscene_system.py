import logging
from collections import deque
from typing import Generator

from cutscene.task import Task
from yazelc import zesper

logger = logging.getLogger(__name__)


class CutsceneSystem(zesper.Processor):
    """
    Runs list of Task types which are coroutines (generators) as a cutscene.
    It is possible to run in parallel more than one list of tasks.
    """

    def __init__(self, *all_task_lists: list[Task]):
        super().__init__()

        self.coroutine_list = dict()
        for task_list in all_task_lists:
            coroutine = self._get_coroutine(task_list)
            self.coroutine_list.update({hex(id(coroutine)): coroutine})
            logger.debug(f'Starting task list: {str(coroutine)}')

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

    def _get_coroutine(self, task_list: list[Task]) -> Generator:
        task_queue = deque(task_list)
        while task_queue:
            task = task_queue.popleft()
            yield from task.run(self.world)

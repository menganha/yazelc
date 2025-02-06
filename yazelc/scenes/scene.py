import abc
from typing import Optional

import pygame

from settings import Settings
from yazelc import save
from yazelc import zesper
from yazelc.controller import Controller
from yazelc.event.event_manager import EventManager
from yazelc.resource_manager import ResourceManager


class BaseScene(abc.ABC):
    """ Base implementation for all scenes  """

    def __init__(self, window: pygame.Surface, controller: Controller, resource_manager: ResourceManager,
                 settings: Settings, state_file: str = None):
        self.window: pygame.Surface = window
        self.controller: Controller = controller
        self.resource_manager: ResourceManager = resource_manager
        self.settings: Settings = settings
        self.state = save.load_state(state_file)

        self.event_manager: EventManager = EventManager()
        self.world: zesper.World = zesper.World()

        self.finished: bool = False
        self.next_scene: Optional[BaseScene] = None
        self.processor_list = list()

    @abc.abstractmethod
    def on_enter(self):
        pass

    def update(self):
        self.event_manager.process_all_events(self.controller, self.processor_list)
        self.world._clear_dead_entities()

    @abc.abstractmethod
    def on_exit(self):
        pass

    def add_processor(self, processor: zesper.Processor, priority: int = 0):
        processor.priority = priority
        self.processor_list.append(processor)
        self.processor_list.sort(key=lambda proc: proc.priority, reverse=True)

    # TODO: Not sure if we will need these at some point
    # def remove_all_processors_except(self, *excluded_processor_types: Type[esper.Processor]) -> list[esper.Processor]:
    #     """ No similar function on the esper Lib."""
    #     processors_to_remove = [proc for proc in self._processors if type(proc) not in excluded_processor_types]
    #     for processor in processors_to_remove:
    #         self._processors.remove(processor)
    #     return processors_to_remove
    #
    # def get_all_processors(self) -> Iterator[Processor]:
    #     """ Get all processors in current world """
    #     for processor in self._processors:
    #         yield processor
    #
    # def clear_processors(self):
    #     self._processors.clear()

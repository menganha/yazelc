import abc

import pygame

from yazelc import save
from yazelc import zesper
from yazelc.controller import Controller
from yazelc.event.event_manager import EventManager
from yazelc.resource_manager import ResourceManager
from yazelc.settings import Settings
from yazelc.systems.player_system import PlayerState


class SceneState:
    def __init__(self):
        self.resources = ResourceManager()
        self.event_manager: EventManager = EventManager()
        self.world: zesper.World = zesper.World()
        self.processor_list: list[zesper.Processor] = list()


class BaseScene(abc.ABC):
    """ Base implementation for all scenes  """

    def __init__(self, window: pygame.Surface, controller: Controller, settings: Settings, save_file: str = None):
        self.window: pygame.Surface = window
        self.controller: Controller = controller
        self.scene_state = SceneState()
        self.settings: Settings = settings
        if save_file:
            self.save = save.load_state(save_file)
        else:
            self.save = PlayerState()

        self.finished: bool = False
        self.next_scene: BaseScene | None = None

    @abc.abstractmethod
    def on_enter(self):
        pass

    def update(self):
        self.scene_state.event_manager.process_all_events(self.controller, self.scene_state.processor_list)
        self.scene_state.world.process()
        for proc in self.scene_state.processor_list:
            proc.process()

    @abc.abstractmethod
    def on_exit(self):
        pass

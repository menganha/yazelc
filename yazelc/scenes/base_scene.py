import abc

import pygame

from yazelc import zesper
from yazelc.controller import Controller
from yazelc.event.event_manager import EventManager
from yazelc.event.event_queue import EventQueue
from yazelc.resource_manager import ResourceManager
from yazelc.settings import Settings
from yazelc.systems.player_system import PlayerState


class SceneState:
    def __init__(self):
        self.resources = ResourceManager()
        self.event_manager: EventManager = EventManager()
        self.world: zesper.World = zesper.World()
        self.processor_list: list[zesper.Processor] = list()
        self.event_queue: EventQueue = EventQueue()  # For its own list of events


class BaseScene(abc.ABC):
    """ Base implementation for all scenes """

    def __init__(self, window: pygame.Surface, controller: Controller, settings: Settings, save_state: PlayerState):
        self.window: pygame.Surface = window
        self.controller: Controller = controller
        self.scene_state = SceneState()
        self.settings: Settings = settings
        self.save_state: PlayerState = save_state

        self.finished: bool = False
        self.next_scene: BaseScene | None = None

    @abc.abstractmethod
    def on_init(self):
        pass

    def update(self):
        self.scene_state.event_manager.process_system_events()
        self.scene_state.event_manager.process_controller(self.controller)

        self.scene_state.event_manager.process_queue(self.scene_state.event_queue)
        if self.scene_state.processor_list:
            for processor in self.scene_state.processor_list:
                self.scene_state.event_manager.process_queue(processor.event_queue)

        self.scene_state.world.process()
        for proc in self.scene_state.processor_list:
            proc.process()

    @abc.abstractmethod
    def on_exit(self):
        pass

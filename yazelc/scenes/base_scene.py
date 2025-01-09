import abc
from typing import Optional

import pygame

from event.events import InputEvent, ChangeSceneEvent
from yazelc import zesper
from yazelc.config import Config
from yazelc.controller import Controller
from yazelc.event.event_manager import EventManager
from yazelc.resource_manager import ResourceManager


class BaseScene(abc.ABC):
    """
    Base implementation for all scenes. This class is abstract and should not be instantiated.
    """

    def __init__(self, window: pygame.Surface, controller: Controller, config: Config, asset_folder: str):
        self.window: pygame.Surface = window
        self.controller: Controller = controller
        self.config: Config = config
        self.resource_manager: ResourceManager = ResourceManager(asset_folder)
        self.event_manager: EventManager = EventManager()
        self.event_queue: EventQueue = EventQueue()
        self.world: zesper.World = zesper.World()

        self.next_scene: Optional['BaseScene'] = None
        self.finished: bool = False
        self.event_manager.subscribe_handler_method(ChangeSceneEvent, self.on_change_scene)

    @abc.abstractmethod
    def on_enter(self):
        pass

    def update(self):
        self._process_event_queue()
        self.world.process()

    @abc.abstractmethod
    def on_exit(self):
        pass

    def on_change_scene(self, change_scene_event: ChangeSceneEvent):
        pass

    def _process_event_queue(self):
        """
        1. Recollect all events from collected on the event queue during the previous frame
        2. Process them all
        3. Process the player input events.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.finished = True
                self.next_scene = None

        self.event_manager.dispatch_queue_events()

        self.controller.process_input()
        input_event = InputEvent(self.controller)
        self.event_manager.dispatch_event(input_event)

import abc
from typing import Optional

import pygame

from yazelc import zesper
from yazelc.controller import Controller
from yazelc.event.event_manager import EventManager
from yazelc.event.event_queue import EventQueue
from yazelc.event.events import InputEvent, ChangeSceneEvent
from yazelc.resource_manager import ResourceManager


class BaseScene(abc.ABC):
    """
    Base implementation for all scenes. This class is abstract and should not be instantiated.
    """

    def __init__(self, window: pygame.Surface, controller: Controller):
        self.window: pygame.Surface = window
        self.resource_manager: ResourceManager = ResourceManager()
        self.event_manager: EventManager = EventManager()
        self.event_queue: EventQueue = EventQueue()
        self.world: zesper.World = zesper.World(self.resource_manager, self.event_queue)
        self.controller: Controller = controller
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

        while self.event_queue:
            event = self.event_queue.popleft()
            self.event_manager.dispatch_event(event)
        self.event_queue.process_delayed_events()

        self.controller.process_input()
        input_event = InputEvent(self.controller)
        self.event_manager.dispatch_event(input_event)

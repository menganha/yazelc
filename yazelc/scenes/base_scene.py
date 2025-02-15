from typing import TypeVar

import pygame

from yazelc import zesper
from yazelc.controller import Controller
from yazelc.event.event_manager import CloseWindowEvent
from yazelc.event.event_manager import EventManager
from yazelc.event.event_queue import EventQueue
from yazelc.resource_manager import ResourceManager
from yazelc.settings import Settings
from yazelc.systems.player_system import PlayerState

ProcessorType = TypeVar('ProcessorType')


class SceneState:
    def __init__(self):
        self.event_manager: EventManager = EventManager()
        self.world: zesper.World = zesper.World()
        self.processor_list: list[zesper.Processor] = list()
        self.event_queue: EventQueue = EventQueue()  # For its own list of events


class Scene:
    """ Basic data structure for all scenes """

    def __init__(self, window: pygame.Surface, controller: Controller, resources: ResourceManager, settings: Settings, save_state: PlayerState):
        self.window: pygame.Surface = window
        self.controller: Controller = controller
        self.resources: ResourceManager = resources
        self.state: SceneState = SceneState()
        self.settings: Settings = settings
        self.save_state: PlayerState = save_state

        self.finished: bool = False
        self.next_scene: Scene | None = None
        # If the scene is finished, it exits directly from the scene stack without falling back to the previous scene
        self.jump_to_exit: bool = False


def on_window_close(scene: Scene, _close_window_event: CloseWindowEvent):
    scene.jump_to_exit = True
    scene.next_scene = None
    scene.finished = True


def update(scene: Scene):
    scene.state.event_manager.process_system_events()
    scene.state.event_manager.process_controller(scene.controller)

    scene.state.event_manager.process_queue(scene.state.event_queue)
    for processor in scene.state.processor_list:
        scene.state.event_manager.process_queue(processor.event_queue)

    scene.state.world.process()
    for proc in scene.state.processor_list:
        proc.process()


def get_processor_instance(scene: Scene, type_: type[ProcessorType]) -> ProcessorType | None:
    for proc in scene.state.processor_list:
        if isinstance(proc, type_):
            return proc
    else:
        return None

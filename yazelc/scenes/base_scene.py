from typing import TypeVar

import pygame

from yazelc import zesper
from yazelc.controller import Controller
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
        self.scene_state: SceneState = SceneState()
        self.settings: Settings = settings
        self.save_state: PlayerState = save_state

        self.finished: bool = False
        self.next_scene: Scene | None = None


def update(scene: Scene):
    scene.scene_state.event_manager.process_system_events()
    scene.scene_state.event_manager.process_controller(scene.controller)

    scene.scene_state.event_manager.process_queue(scene.scene_state.event_queue)
    for processor in scene.scene_state.processor_list:
        scene.scene_state.event_manager.process_queue(processor.event_queue)

    scene.scene_state.world.process()
    for proc in scene.scene_state.processor_list:
        proc.process()


def get_processor_instance(scene: Scene, type_: type[ProcessorType]) -> ProcessorType | None:
    for proc in scene.scene_state.processor_list:
        if isinstance(proc, type_):
            return proc
    else:
        return None

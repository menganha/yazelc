import logging.config

import pygame
import pygame.freetype
from controller import ButtonReleasedEvent

pygame.init()

import zesper
from event.event_manager import EventManager, CloseWindowEvent
from yazelc.controller import ButtonDownEvent, Button

from settings import Settings
from yazelc.logging_config import DBG_CONFIG
from yazelc.resource_manager import ResourceManager
from yazelc.systems.render_system import RenderSystem
from yazelc.systems.animation_system import AnimationSystem
from yazelc.components import Renderable, Position
from yazelc.keyboard import Keyboard
from yazelc.systems.player_system import PlayerSystem, PlayerState
from dataclasses import dataclass, field


@dataclass()
class GameState:
    # This is something like the state of the world. Maybe is something to gather in an own type. This is what
    # must be serialized in order to recover (load state) the entire state of the world
    resources = ResourceManager('../../')
    event_manager = EventManager()
    world = zesper.World()
    system_list: list[zesper.Processor] = field(default_factory=list)


class Game:

    def __init__(self):
        self.is_running = True
        self.reset = False
        self.waiting_for_close_dialog = False
        self.config = Settings.load_from_json('../../data/settings.json', window={'bgcolor': pygame.Color(255, 255, 255)})
        self.window = pygame.display.set_mode(self.config.window.resolution, pygame.SCALED, vsync=1)
        self.controller = Keyboard()
        self.game_state = GameState()
        self.initialize()

    def initialize(self):
        # Setting all systems
        render_system = RenderSystem(self.window, self.config.window.bgcolor, self.game_state.world)
        animation_system = AnimationSystem(self.game_state.world, self.game_state.resources)
        player_system = PlayerSystem(self.config.player, PlayerState().inventory, self.game_state.world, self.game_state.resources)
        self.game_state.system_list = [player_system, animation_system, render_system]

        # Message box
        font = self.game_state.resources.font('assets/font/Px437_Portfolio_6x8.ttf', pygame.Color('blue'), 8)
        msg = 'Character Demo'
        surface = font.render(msg)
        self.game_state.world.create_entity(Renderable(surface), Position(10, 10))

        # Subscribe all events
        self.game_state.event_manager.subscribe(CloseWindowEvent, self.on_window_closed)
        self.game_state.event_manager.subscribe(ButtonDownEvent, player_system.on_button_down)
        self.game_state.event_manager.subscribe(ButtonDownEvent, self.on_button_down)
        self.game_state.event_manager.subscribe(ButtonReleasedEvent, player_system.on_button_released)

    def on_window_closed(self, _close_window_event: CloseWindowEvent):
        self.is_running = False

    def on_button_down(self, event: ButtonDownEvent):
        if event.button == Button.START:
            self.reset = True

    def run(self):
        while self.is_running:
            self.game_state.event_manager.process_all_events(self.controller, self.game_state.system_list)
            self.game_state.world.process()
            for processor in self.game_state.system_list:
                processor.process()
            if self.reset:
                self.initialize()
                self.reset = False
        pygame.quit()


if __name__ == '__main__':
    logging.config.dictConfig(DBG_CONFIG)
    app = Game()
    app.run()

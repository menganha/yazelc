import pygame
import pygame.freetype

pygame.init()

import zesper
from event.event_manager import EventManager, ButtonDownEvent, CloseWindowEvent

from settings import Settings
from yazelc.resource_manager import ResourceManager
from yazelc.systems.render_system import RenderSystem
from yazelc.systems.animation_system import AnimationSystem
from yazelc.components import Animation, Renderable, Position
from yazelc.keyboard import Keyboard, Button
from yazelc.animation import AnimationState, AnimationDirection


class Game:
    def __init__(self):
        self.is_running = True
        self.waiting_for_close_dialog = False

        self.config = Settings.load_from_json('../settings.json', window={'bgcolor': pygame.Color(255, 255, 255)})
        self.resource_manager = ResourceManager('../../')
        self.event_manager = EventManager()
        self.world = zesper.World()
        self.controller = Keyboard()
        self.window = pygame.display.set_mode(self.config.window.resolution, pygame.SCALED, vsync=1)

        self.animation_data = self.resource_manager.animation('data/animation/player.json')

        render_system = RenderSystem(self.window, self.config.window.bgcolor, self.world)
        animation_system = AnimationSystem(self.world, self.resource_manager)
        self.system_list = [render_system, animation_system]

        start_sequence = self.animation_data.get_sequence(AnimationState.WALKING, AnimationDirection.DOWN)
        start_image = self.resource_manager.image(start_sequence.get_image_id(0))
        position = Position(self.config.window.resolution.x // 2, self.config.window.resolution.y // 2)
        self.character = self.world.create_entity(position, Renderable(start_image), Animation(start_sequence))

        # Message box
        font = self.resource_manager.font('assets/font/Px437_Portfolio_6x8.ttf', pygame.Color('blue'), 8)
        msg = 'Press the arrow keys to change\nthe animation direction'

        surface = font.render(msg)
        self.world.create_entity(Renderable(surface), Position(10, 10))

        self.event_manager.subscribe(CloseWindowEvent, self.on_window_closed)
        self.event_manager.subscribe(ButtonDownEvent, self.on_button_down)

    def on_button_down(self, button_event: ButtonDownEvent):
        if button_event.button == Button.LEFT:
            sequence = self.animation_data.get_sequence(AnimationState.WALKING, AnimationDirection.LEFT)
            self.world.add_component(self.character, Animation(sequence))
        if button_event.button == Button.RIGHT:
            sequence = self.animation_data.get_sequence(AnimationState.WALKING, AnimationDirection.RIGHT)
            self.world.add_component(self.character, Animation(sequence))
        if button_event.button == Button.DOWN:
            sequence = self.animation_data.get_sequence(AnimationState.WALKING, AnimationDirection.DOWN)
            self.world.add_component(self.character, Animation(sequence))
        if button_event.button == Button.UP:
            sequence = self.animation_data.get_sequence(AnimationState.WALKING, AnimationDirection.UP)
            self.world.add_component(self.character, Animation(sequence))

    def on_window_closed(self, _close_window_event: CloseWindowEvent):
        self.is_running = False

    def run(self):
        while self.is_running:
            self.event_manager.process_all_events(self.controller, self.system_list)
            self.world.process()
            for processor in self.system_list:
                processor.process()
        pygame.quit()


if __name__ == '__main__':
    app = Game()
    app.run()

import pygame
import pygame.freetype

pygame.init()

import zesper
from event.event_manager import EventManager, ButtonDownEvent, CloseWindowEvent

from settings import Settings
from yazelc.resource_manager import ResourceManager
from yazelc.systems.render_system import RenderSystem
from yazelc.systems.kinetic_system import KineticSystem
from yazelc.systems.collision_system import CollisionSystem
from yazelc.components import Renderable, Position, HitBox
from yazelc.keyboard import Keyboard, Button
from yazelc.camera import Camera
from yazelc.map import Map


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

        overworld_map_path = self.resource_manager.find_file('overworld-x00-y00.tmx')
        map_ = Map(overworld_map_path, self.resource_manager)
        for image, depth in map_.get_map_images():
            self.world.create_entity(Position(), Renderable(image, depth=depth))

        # Controlled rect
        image = pygame.Surface((16, 16))
        image.fill('red')
        renderable = Renderable(image)
        position = Position(10, 10)
        hitbox = HitBox(10, 10, 16, 16)
        self.character = self.world.create_entity(position, renderable, hitbox)

        # Camera
        camera = Camera(self.config.window.resolution, map_.size)
        camera.track_entity(self.character, self.world)

        movement_system = KineticSystem(self.world)
        collision_system = CollisionSystem(self.world)
        render_system = RenderSystem(self.window, self.config.window.bgcolor, self.world, camera)
        self.system_list = [movement_system, collision_system, render_system]

        # Message box
        font = self.resource_manager.font('assets/font/Px437_Portfolio_6x8.ttf', pygame.Color('blue'), 8)
        msg = 'Map Testing. Press Start to restart'
        surface = font.render(msg)
        self.world.create_entity(Renderable(surface), Position(0, 0))

        # Subscribe to events
        self.event_manager.subscribe(ButtonDownEvent, self.on_button_down)
        self.event_manager.subscribe(CloseWindowEvent, self.on_window_closed)

    def on_button_down(self, button_event: ButtonDownEvent):
        position = self.world.component_for_entity(self.character, Position)
        hitbox = self.world.component_for_entity(self.character, HitBox)
        # This tiny delta ensures that the rounding produces the displacement pattern 1,2,1,2...
        # per frame that averages a velocity of 1.5
        velocity = 1  # .5 - 1e-8
        if button_event.button == Button.LEFT:
            position.x -= velocity
        if button_event.button == Button.RIGHT:
            position.x += velocity
        if button_event.button == Button.UP:
            position.y -= velocity
        if button_event.button == Button.DOWN:
            position.y += velocity
        hitbox.x = round(position.x)
        hitbox.y = round(position.y)

        if button_event.button == Button.START:
            self.restart()

    def on_window_closed(self, close_window_event: CloseWindowEvent):
        self.is_running = False

    def restart(self):
        self.event_manager.remove_handlers()
        self.world.clear_database()
        self.__init__()

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

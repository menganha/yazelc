import pygame
import pygame.freetype

pygame.init()

import zesper
from event.event_manager import EventManager, ButtonDownEvent, CloseWindowEvent, ButtonReleasedEvent

from yazelc.config import Config
from yazelc.resource_manager import ResourceManager
from yazelc.systems.render_system import RenderSystem
from yazelc.systems.movement_system import MovementSystem, EndMovementEvent
from yazelc.systems.collision_system import CollisionSystem, EnterCollisionEvent, ExitCollisionEvent, SolidEnterCollisionEvent, SolidExitCollisionEvent, HitboxSquishedEvent
from yazelc.components import Renderable, Position, HitBox, Move
from yazelc.keyboard import Keyboard, Button
from yazelc.utils.game_utils import IVec
import logging

logger = logging.getLogger(__name__)


class Game:
    def __init__(self):
        self.is_running = True
        self.waiting_for_close_dialog = False

        self.config = Config.load_from_json('../settings.json', window={'bgcolor': pygame.Color(255, 255, 255)})
        self.resource_manager = ResourceManager()
        self.event_manager = EventManager()
        self.world = zesper.World()
        self.controller = Keyboard()
        self.window = pygame.display.set_mode(self.config.window.resolution, pygame.SCALED, vsync=1)

        movement_system = MovementSystem()
        collision_system = CollisionSystem()
        render_system = RenderSystem(self.window, self.config)

        self.world.add_processor(movement_system)  # Order matters here
        self.world.add_processor(collision_system)
        self.world.add_processor(render_system)

        image = pygame.Surface((16, 16))
        image.fill('red')
        renderable = Renderable(image)
        position = Position(0, 119)
        hitbox = HitBox(0, 0, 16, 16)
        self.character = self.world.create_entity(position, renderable, hitbox)
        # Message box
        font = self.resource_manager.font('Px437_Portfolio_6x8.ttf', pygame.Color('blue'), 8)
        msg = 'Collision Testing. Press Start to restart'
        surface = font.render(msg)
        self.world.create_entity(Renderable(surface), Position(0, 0))

        # Message box for collision notifications Solids
        self.solid_collision_entity: int | None = None
        font = self.resource_manager.font('Px437_Portfolio_6x8.ttf', pygame.Color('red'), 8)
        msg = 'Collided with Solid'
        self.collision_msg_surface_solid = font.render(msg)

        # Message box for collision notifications
        self.non_solid_collision_entity: int | None = None
        font = self.resource_manager.font('Px437_Portfolio_6x8.ttf', pygame.Color('green'), 8)
        msg = 'Colliding with non-Solid'
        self.collision_msg_surface = font.render(msg)

        # Squished message box
        font = self.resource_manager.font('Px437_Portfolio_6x8.ttf', pygame.Color('red'), 8)
        msg = 'Squished!!!'
        self.squished_msg_surface = font.render(msg)

        # Wall
        image = pygame.Surface((20, 20))
        image.fill('black')
        renderable = Renderable(image)
        position = Position(50, 130)
        hitbox = HitBox(50, 130, 20, 20, solid=True)
        self.world.create_entity(position, renderable, hitbox)

        # Non-Solid Component
        image = pygame.Surface((10, 10))
        renderable = Renderable(image)
        image.fill('pink')
        self.world.create_entity(Position(10, 50), HitBox(10, 50, 10, 10), renderable)
        self.world.create_entity(Position(200, 70), HitBox(200, 70, 10, 10), renderable)

        # Moving Wall
        image = pygame.Surface((20, 20))
        image.fill('black')
        renderable = Renderable(image)
        position = Position(200, 130)
        hitbox = HitBox(200, 130, 20, 20, solid=True)
        move = Move(1.0, IVec(70, 130))
        self.phase = True
        self.world.create_entity(position, renderable, hitbox, move)

        # Subscribe to events
        self.event_manager.subscribe(EndMovementEvent, self.on_movement_end)
        self.event_manager.subscribe(CloseWindowEvent, self.on_window_closed)
        self.event_manager.subscribe(ButtonDownEvent, self.on_button_down)
        self.event_manager.subscribe(ButtonReleasedEvent, self.on_button_released)

        self.event_manager.subscribe(SolidEnterCollisionEvent, self.on_solid_enter_collision)
        self.event_manager.subscribe(SolidExitCollisionEvent, self.on_solid_exit_collision)

        self.event_manager.subscribe(EnterCollisionEvent, self.on_enter_collision)
        self.event_manager.subscribe(ExitCollisionEvent, self.on_exit_collision)

        self.event_manager.subscribe(HitboxSquishedEvent, self.on_squished)

    def on_button_down(self, button_event: ButtonDownEvent):
        position = self.world.component_for_entity(self.character, Position)
        hitbox = self.world.component_for_entity(self.character, HitBox)
        # This tiny delta ensures that the rounding produces the displacement pattern 1,2,1,2...
        # per frame that averages a velocity of 1.5
        velocity = 1.5 - 1e-8
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

    def restart(self):
        self.event_manager.remove_all_handlers()
        self.world.clear_database()
        self.__init__()

    def on_movement_end(self, end_movement_event: EndMovementEvent):
        goal = IVec(200, 130) if self.phase else IVec(70, 130)
        move = Move(1.0, goal)
        self.world.add_component(end_movement_event.ent, move)
        self.phase = not self.phase

    def on_button_released(self, button_event: ButtonReleasedEvent):
        position = self.world.component_for_entity(self.character, Position)
        if button_event.button in (Button.LEFT, Button.RIGHT, Button.UP, Button.DOWN):
            position.x = round(position.x)
            position.y = round(position.y)

    def on_solid_enter_collision(self, collision_event: SolidEnterCollisionEvent):
        if self.solid_collision_entity is None:
            self.solid_collision_entity = self.world.create_entity(
                Renderable(self.collision_msg_surface_solid),
                Position(0, 10)
            )

    def on_solid_exit_collision(self, collision_event: SolidEnterCollisionEvent):
        self.world.delete_entity(self.solid_collision_entity)
        self.solid_collision_entity = None

    def on_enter_collision(self, collision_event: EnterCollisionEvent):
        if self.non_solid_collision_entity is None:
            self.non_solid_collision_entity = self.world.create_entity(
                Renderable(self.collision_msg_surface),
                Position(0, 20)
            )

    def on_exit_collision(self, collision_event: ExitCollisionEvent):
        self.world.delete_entity(self.non_solid_collision_entity)
        self.non_solid_collision_entity = None

    def on_window_closed(self, close_window_event: CloseWindowEvent):
        self.is_running = False

    def on_squished(self, squished_event: HitboxSquishedEvent):
        self.world.create_entity(Renderable(self.squished_msg_surface), Position(0, 20))

    def run(self):
        while self.is_running:
            self.event_manager.process_all_events(self.controller, self.world)
            self.world.process()
        pygame.quit()


if __name__ == '__main__':
    app = Game()
    app.run()

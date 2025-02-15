import pygame
import pygame.freetype

pygame.init()

from yazelc import zesper
from yazelc.event.event_manager import EventManager, ButtonDownEvent, CloseWindowEvent, ButtonReleasedEvent

from yazelc.settings import Settings
from yazelc.resource_manager import ResourceManager
from yazelc.systems.render_system import RenderSystem
from yazelc.systems.kinetic_system import KineticSystem, EndMovementEvent
from yazelc.systems.collision_system import CollisionSystem, EnterCollisionEvent, ExitCollisionEvent, SolidEnterCollisionEvent, SolidExitCollisionEvent, HitboxSquishedEvent
from yazelc.components import Renderable, Position, HitBox, Move, Velocity
from yazelc.keyboard import Keyboard, Button
from yazelc.utils.game_utils import IVec


class Game:
    def __init__(self):
        self.is_running = True
        self.waiting_for_close_dialog = False

        self.config = Settings.load_from_json('../../data/settings.json', window={'bgcolor': pygame.Color(255, 255, 255)})
        self.resource_manager = ResourceManager('../../')
        self.event_manager = EventManager()
        self.world = zesper.World()
        self.controller = Keyboard()
        self.window = pygame.display.set_mode(self.config.window.resolution, pygame.SCALED, vsync=1)

        movement_system = KineticSystem(self.world)
        collision_system = CollisionSystem(self.world)
        render_system = RenderSystem(self.window, self.config.window.bgcolor, self.world)
        self.system_list = [movement_system, collision_system, render_system]

        image = pygame.Surface((16, 16))
        image.fill('red')
        renderable = Renderable(image)
        position = Position(0, 119)
        hitbox = HitBox(0, 0, 16, 16)
        self.character = self.world.create_entity(position, renderable, hitbox)

        font = self.resource_manager.font('assets/font/Px437_Portfolio_6x8.ttf', pygame.Color('blue'), 8)
        font_red = self.resource_manager.font('assets/font/Px437_Portfolio_6x8.ttf', pygame.Color('red'), 8)
        # Message box
        msg = 'Collision Testing. Press Start to restart'
        surface = font.render(msg)
        self.world.create_entity(Renderable(surface), Position(0, 0))

        # Message box for collision notifications Solids
        self.solid_collision_entity: int | None = None
        msg = 'Collided with Solid!'
        self.collision_msg_surface_solid = font_red.render(msg)

        # Message box for collision notifications
        self.non_solid_collision_entity: int | None = None
        msg = 'Colliding with non-Solid...'
        self.collision_msg_surface = font_red.render(msg)

        # Squished message box
        msg = 'You have been Squished!!!!'
        self.squished_msg_surface = font_red.render(msg)

        # Walls
        image = pygame.Surface((20, 20))
        image.fill('black')
        renderable = Renderable(image)

        position = Position(50, 130)
        hitbox = HitBox(50, 130, 20, 20, solid=True)
        self.world.create_entity(position, renderable, hitbox)

        position = Position(100, 50)
        hitbox = HitBox(int(position.x), int(position.y), 20, 20, solid=True)
        self.world.create_entity(position, renderable, hitbox)

        # Non-Solid boxes
        image = pygame.Surface((10, 10))
        renderable = Renderable(image)
        image.fill('pink')

        # NOTE: The Hitbox position doesn't matter as it gets updated once the hitboxes start moving
        vel = 0.1
        self.world.create_entity(Position(80, 41), HitBox(10, 41, 10, 10, skin_depth=3), Velocity(vel, 0), renderable)
        self.world.create_entity(Position(300, 41), HitBox(10, 41, 10, 10, skin_depth=3), Velocity(-vel, 0), renderable)
        self.world.create_entity(Position(80, 69), HitBox(10, 41, 10, 10, skin_depth=3), Velocity(vel, 0), renderable)
        self.world.create_entity(Position(300, 69), HitBox(10, 41, 10, 10, skin_depth=3), Velocity(-vel, 0), renderable)

        self.world.create_entity(Position(91, 120), HitBox(10, 41, 10, 10, skin_depth=3), Velocity(0, -vel), renderable)
        self.world.create_entity(Position(119, 120), HitBox(10, 41, 10, 10, skin_depth=3), Velocity(0, -vel), renderable)
        self.world.create_entity(Position(91, -50), HitBox(10, 41, 10, 10, skin_depth=3), Velocity(0, vel), renderable)
        self.world.create_entity(Position(119, -50), HitBox(10, 41, 10, 10, skin_depth=3), Velocity(0, vel), renderable)

        # Diagonal movement
        self.world.create_entity(Position(60, 100), HitBox(10, 41, 10, 10, skin_depth=0), Velocity(vel, -vel), renderable)

        # Other non-moving non-solid hitboxes
        self.world.create_entity(Position(10, 200), HitBox(10, 50, 10, 10), renderable)
        self.world.create_entity(Position(200, 220), HitBox(200, 70, 10, 10), renderable)

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
        velocity = 1
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
        self.event_manager.remove_handlers()
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

    def on_solid_enter_collision(self, _collision_event: SolidEnterCollisionEvent):
        if _collision_event.ent == self.character and self.solid_collision_entity is None:
            self.solid_collision_entity = self.world.create_entity(
                Renderable(self.collision_msg_surface_solid),
                Position(0, 10)
            )

    def on_solid_exit_collision(self, _collision_event: SolidExitCollisionEvent):
        if _collision_event.ent == self.character:
            self.world.delete_entity(self.solid_collision_entity)
            self.solid_collision_entity = None

    def on_enter_collision(self, _collision_event: EnterCollisionEvent):
        collided_with_char = _collision_event.ent_1 == self.character or _collision_event.ent_2 == self.character
        if collided_with_char and self.non_solid_collision_entity is None:
            self.non_solid_collision_entity = self.world.create_entity(
                Renderable(self.collision_msg_surface),
                Position(0, 20)
            )

    def on_exit_collision(self, _collision_event: ExitCollisionEvent):
        collided_with_char = _collision_event.ent_1 == self.character or _collision_event.ent_2 == self.character
        if collided_with_char:
            self.world.delete_entity(self.non_solid_collision_entity)
            self.non_solid_collision_entity = None

    def on_window_closed(self, _close_window_event: CloseWindowEvent):
        self.is_running = False

    def on_squished(self, _squished_event: HitboxSquishedEvent):
        self.world.create_entity(Renderable(self.squished_msg_surface), Position(0, 20))

    def run(self):
        while self.is_running:
            self.event_manager.process_system_events()
            self.event_manager.process_controller(self.controller)
            for processor in self.system_list:
                self.event_manager.process_queue(processor.event_queue)
            self.world.process()
            for processor in self.system_list:
                processor.process()
        pygame.quit()


if __name__ == '__main__':
    app = Game()
    app.run()

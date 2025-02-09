import logging
from dataclasses import dataclass, field

from yazelc import components as cmp
from yazelc.animation import EntityState, EntityDirection
from yazelc.controller import Button, ButtonDownEvent, ButtonReleasedEvent, ButtonPressedEvent
from yazelc.event.events import eventclass
from yazelc.resource_manager import ResourceManager
from yazelc.settings import PlayerConfig
from yazelc.systems.collision_system import SolidEnterCollisionEvent, EnterCollisionEvent
from yazelc.zesper import World, Processor

logger = logging.getLogger(__name__)


@eventclass
class DialogTriggerEvent:
    sign_ent_id: int


@eventclass
class EnterDoorEvent:
    map: str


@dataclass
class Inventory:
    """
     4 hearth pieces form a total heart and each heart corresponds to two health points
    """
    heart_pieces: int = 12
    health: int = 6
    weapons: list = field(default_factory=list)


@dataclass
class PlayerState:
    inventory: Inventory = field(default_factory=Inventory)
    last_visited_map: str = "data/map/overworld/overworld-x00-y00.tmx"
    # TODO: Here we add everything that can be taken away from the player, like different items weapons, etc.
    #   We could serialize this to be part of a save state later on


class PlayerSystem(Processor):

    def __init__(self, player_config: PlayerConfig, inventory: Inventory, world: World,
                 resource_manager: ResourceManager):
        super().__init__()

        animation_data = resource_manager.animation(player_config.animation)
        start_sequence = animation_data.get_sequence(EntityState.MOVING, EntityDirection.DOWN)
        start_image = resource_manager.image(start_sequence.get_image_id(0))

        renderable = cmp.Renderable(start_image, depth=player_config.sprite_depth)
        hitbox = cmp.HitBox(0, 0, *player_config.hitbox_size, False, *player_config.hitbox_offset,
                            skin_depth=player_config.skin_depth
                            )
        position = cmp.Position()
        health = cmp.Health(inventory.health, inventory.heart_pieces // 4)

        self.player_entity = world.create_entity(renderable, hitbox, position, health)
        self.player_config = player_config

        self.resource_manager = resource_manager
        self.world = world

        self.velocity = cmp.Vec()
        self.direction = EntityDirection.DOWN
        self.directional_key_released = True  # To aid in the check of a direction change
        self.interaction_box_entity = self.world.create_entity()

    def process(self):
        """ Normalizes velocity, moves and handles animation """

        if int(self.velocity.x) != 0 and int(self.velocity.y) != 0:  # Normalize velocity
            sign = int(0 < self.velocity.x) - int(self.velocity.x < 0)
            self.velocity.x = self.player_config.velocity_diagonal * sign

            sign = int(0 < self.velocity.y) - int(self.velocity.y < 0)
            self.velocity.y = self.player_config.velocity_diagonal * sign

        position = self.world.component_for_entity(self.player_entity, cmp.Position)
        hitbox = self.world.component_for_entity(self.player_entity, cmp.HitBox)

        position.x += self.velocity.x
        position.y += self.velocity.y
        hitbox.x = int(position.x + hitbox.offset.x)
        hitbox.y = int(position.y + hitbox.offset.y)

        # Animation handling
        not_moving = int(self.velocity.x) == 0 and int(self.velocity.y) == 0
        has_animation = self.world.has_component(self.player_entity, cmp.Animation)
        if not_moving:
            if has_animation:  # Get the starting frame and set it to the renderable image
                animation = self.world.component_for_entity(self.player_entity, cmp.Animation)
                renderable = self.world.component_for_entity(self.player_entity, cmp.Renderable)
                renderable.image = self.resource_manager.image(animation.sequence.get_image_id(0))
                self.world.remove_component(self.player_entity, cmp.Animation)
        else:
            logger.debug(f'movement step '
                         f'{round(position.x) - round(position.prev_x)}, '
                         f'{round(position.y) - round(position.prev_y)}'
                         )

            # Check change of entity direction
            old_direction = self.direction

            if self.player_config.prefer_up_down_animation or self.directional_key_released or not has_animation:
                if int(self.velocity.x) < 0:
                    self.direction = EntityDirection.LEFT
                elif int(self.velocity.x) > 0:
                    self.direction = EntityDirection.RIGHT

                if int(self.velocity.y) < 0:
                    self.direction = EntityDirection.UP
                elif int(self.velocity.y) > 0:
                    self.direction = EntityDirection.DOWN

            if old_direction != self.direction or not has_animation:
                animation_data = self.resource_manager.animation(self.player_config.animation)
                sequence = animation_data.get_sequence(EntityState.MOVING, self.direction)
                self.world.add_component(self.player_entity, cmp.Animation(sequence))

        self.velocity.x, self.velocity.y = 0, 0
        self.directional_key_released = False

    def set_position(self, pos_x: int, pos_y: int):
        new_position = cmp.Position(pos_x, pos_y)
        self.world.add_component(self.player_entity, new_position)

    def on_button_down(self, button_event: ButtonDownEvent):
        if button_event.button == Button.LEFT:
            self.velocity.x -= self.player_config.velocity
        elif button_event.button == Button.RIGHT:
            self.velocity.x += self.player_config.velocity
        elif button_event.button == Button.DOWN:
            self.velocity.y += self.player_config.velocity
        elif button_event.button == Button.UP:
            self.velocity.y -= self.player_config.velocity

    def on_button_pressed(self, button_event: ButtonPressedEvent):
        if button_event.button == Button.A:
            # Create an interaction box
            player_hitbox = self.world.component_for_entity(self.player_entity, cmp.HitBox)
            hitbox = cmp.HitBox(0, 0, 4, 5)  # TODO: Remove this magic numbers
            if self.direction == EntityDirection.UP:
                hitbox.bottom = player_hitbox.top
                hitbox.centerx = player_hitbox.centerx
            elif self.direction == EntityDirection.LEFT:
                hitbox.right = player_hitbox.left
                hitbox.centery = player_hitbox.centery
            elif self.direction == EntityDirection.RIGHT:
                hitbox.left = player_hitbox.right
                hitbox.centery = player_hitbox.centery
            elif self.direction == EntityDirection.DOWN:
                hitbox.top = player_hitbox.bottom
                hitbox.centerx = player_hitbox.centerx
            self.world.add_component(self.interaction_box_entity, hitbox)

    def on_button_released(self, button_event: ButtonReleasedEvent):
        position = self.world.component_for_entity(self.player_entity, cmp.Position)
        if button_event.button == Button.LEFT or button_event.button == button_event.button.RIGHT:
            position.x = round(position.x)
            self.directional_key_released = True
        elif button_event.button == Button.UP or button_event.button == button_event.button.DOWN:
            position.y = round(position.y)
            self.directional_key_released = True

    def on_solid_collision(self, collision_event: SolidEnterCollisionEvent):
        if collision_event.ent == self.interaction_box_entity and self.world.try_component(collision_event.ent_solid, cmp.Sign):
            self.event_queue.add(DialogTriggerEvent(collision_event.ent_solid))
            self.world.remove_component(self.interaction_box_entity, cmp.HitBox)

    def on_collision(self, collision_event: EnterCollisionEvent):
        if res := self.world.try_signature(collision_event.ent_1, collision_event.ent_2, cmp.Door):
            ent_door, door, ent = res
            if ent == self.player_entity:
                self.event_queue.add(EnterDoorEvent(door.target_map))

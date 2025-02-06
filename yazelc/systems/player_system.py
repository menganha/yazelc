import logging
from dataclasses import dataclass

from yazelc import components as cmp
from yazelc.animation import AnimationState, AnimationDirection
from yazelc.controller import Button, ButtonDownEvent, ButtonReleasedEvent
from yazelc.resource_manager import ResourceManager
from yazelc.settings import PlayerConfig
from yazelc.zesper import World, Processor

logger = logging.getLogger(__name__)


@dataclass
class Inventory:
    """
     4 hearth pieces form a total heart and each heart corresponds to two health points
    """
    heart_pieces: int = 12
    health: int = 6
    weapons: list = None
    # TODO: Here we add everything that can be taken away from the player, like different items weapons, etc.
    #   We could serialize this to be part of a save state later on


class PlayerSystem(Processor):

    def __init__(self, player_config: PlayerConfig, inventory: Inventory, world: World,
                 resource_manager: ResourceManager):

        """
        movement type 0: UP and down animations are going to take precedence when moving diagonally
        movement type 1: Animation set at the beginning of movement is hold
        """
        super().__init__()

        animation_data = resource_manager.animation(player_config.animation)
        start_sequence = animation_data.get_sequence(AnimationState.WALKING, AnimationDirection.DOWN)
        start_image = resource_manager.image(start_sequence.get_image_id(0))

        renderable = cmp.Renderable(start_image, depth=player_config.sprite_depth)
        hitbox = cmp.HitBox(0, 0, *player_config.hitbox_size, skin_depth=player_config.skin_depth)
        position = cmp.Position()
        health = cmp.Health(inventory.health, inventory.heart_pieces // 4)

        self.player_entity = world.create_entity(renderable, hitbox, position, health)
        self.player_config = player_config

        self.resource_manager = resource_manager
        self.world = world

        self.velocity = cmp.Vec()
        self.direction = AnimationDirection.NONE

        self.movement_type = 0

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
        hitbox.x = int(position.x)
        hitbox.y = int(position.y)

        # Animation handling
        not_moving = int(self.velocity.x) == 0 and int(self.velocity.y) == 0
        has_animation = self.world.has_component(self.player_entity, cmp.Animation)
        if not_moving:
            self.direction = AnimationDirection.NONE
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

            # Attempt to change the animation
            old_direction = self.direction
            if (self.movement_type == 0 and old_direction != AnimationDirection.NONE) or self.movement_type != 0:
                if int(self.velocity.x) < 0:
                    self.direction = AnimationDirection.LEFT
                elif int(self.velocity.x) > 0:
                    self.direction = AnimationDirection.RIGHT

                if int(self.velocity.y) < 0:
                    self.direction = AnimationDirection.UP
                elif int(self.velocity.y) > 0:
                    self.direction = AnimationDirection.DOWN

            if old_direction != self.direction:
                animation_data = self.resource_manager.animation(self.player_config.animation)
                sequence = animation_data.get_sequence(AnimationState.WALKING, self.direction)
                self.world.add_component(self.player_entity, cmp.Animation(sequence))

        self.velocity.x, self.velocity.y = 0, 0

    def on_button_down(self, button_event: ButtonDownEvent):
        if button_event.button == Button.LEFT:
            self.velocity.x -= self.player_config.velocity
        if button_event.button == Button.RIGHT:
            self.velocity.x += self.player_config.velocity
        if button_event.button == Button.DOWN:
            self.velocity.y += self.player_config.velocity
        if button_event.button == Button.UP:
            self.velocity.y -= self.player_config.velocity

    def on_button_released(self, button_event: ButtonReleasedEvent):
        position = self.world.component_for_entity(self.player_entity, cmp.Position)
        if button_event.button == Button.LEFT or button_event.button == button_event.button.RIGHT:
            position.x = round(position.x)
        if button_event.button == Button.UP or button_event.button == button_event.button.DOWN:
            position.y = round(position.y)

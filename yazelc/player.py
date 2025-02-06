"""
The module gathers functions that add commonly used entities to an input world
"""

from yazelc import components as cmp
from yazelc import weapons
from yazelc import zesper
from yazelc.event.events import DeleteEntityEvent
from yazelc.utils.game_utils import Status


# def get_position_of_sprite(hitbox: cmp.HitBox):
#     """ Gets the position of the sprite from the player's Hitbox """
#     relative_pos_x = SPRITE_SIZE // 2
#     relative_pos_y = SPRITE_SIZE // 2 + HITBOX_Y_OFFSET
#     return hitbox.centerx - relative_pos_x, hitbox.centery - relative_pos_y
#
#
# def get_position_of_hitbox(sprite_position: cmp.Position):
#     """ Gets the position of the center hitbox from the player's position """
#     relative_pos_x = SPRITE_SIZE // 2
#     relative_pos_y = SPRITE_SIZE // 2 + HITBOX_Y_OFFSET
#     return sprite_position.x + relative_pos_x, sprite_position.y + relative_pos_y


def drop_bomb(player_entity_id: int, world: zesper.World):
    position = world.component_for_entity(player_entity_id, cmp.Position)
    direction = world.component_for_entity(player_entity_id, cmp.State).direction
    renderable = world.component_for_entity(player_entity_id, cmp.Renderable)

    bomb_position_center_x = position.x + renderable.width // 2 + direction.value.x * 8
    bomb_position_center_y = position.y + renderable.height // 2 + direction.value.y * 8
    bomb_position = cmp.Position(bomb_position_center_x - weapons.BOMB_SPRITE_WIDTH // 2,
                                 bomb_position_center_y - weapons.BOMB_SPRITE_WIDTH // 2
                                 )

    weapons.create_bomb(bomb_position, world)


def create_melee_weapon(player_entity_id: int, world: zesper.World):
    """ Creates a Weapon hitbox for the parent entity with a hitbox """

    weapon_entity_id = world.create_entity()

    hitbox = _create_hitbox_in_front(player_entity_id, SWORD_FRONT_RANGE, SWORD_SIDE_RANGE, world)
    world.add_component(weapon_entity_id, hitbox)

    # world.add_component(hitbox_entity_id, hitbox)
    world.add_component(weapon_entity_id,
                        cmp.Weapon(damage=SWORD_DAMAGE, active_frames=SWORD_ACTIVE_FRAMES,
                                   freeze_frames=SWORD_FREEZE_FRAMES,
                                   recoil_velocity=SWORD_RECOIL_VEL
                                   )
                        )

    direction = world.component_for_entity(player_entity_id, cmp.State).direction
    strip = world.resource_manager.get_animation_strip(f'wooden_sword_{direction.name}')
    world.add_component(weapon_entity_id, cmp.Animation.from_delay(strip, ATTACK_ANIMATION_DELAY, one_loop=True))
    world.add_component(weapon_entity_id, cmp.Renderable(strip[0], SPRITE_DEPTH + 1))
    player_position = world.component_for_entity(player_entity_id, cmp.Position)
    weapon_position_x = player_position.x - (SWORD_SPRITE_WIDTH - SPRITE_SIZE) // 2
    weapon_position_y = player_position.y - (SWORD_SPRITE_WIDTH - SPRITE_SIZE) // 2
    world.add_component(weapon_entity_id, cmp.Position(weapon_position_x, weapon_position_y))


def create_interactive_hitbox(player_entity_id: int, world: zesper.World):
    """ Creates a hitbox to detect interaction with other objects """

    entity_id = world.create_entity()

    hitbox = _create_hitbox_in_front(player_entity_id, INTERACTIVE_FRONT_RANGE, INTERACTIVE_SIDE_RANGE, world)

    world.add_component(entity_id, hitbox)
    world.add_component(entity_id, cmp.InteractorTag())
    world.event_queue.add(DeleteEntityEvent(entity_id), frames_delay=1)


def handle_animation_for_input(ent_id: int, state: cmp.State, world: zesper.World):
    animation_identifier = world.resource_manager.get_animation_identifier(SPRITE_SHEET_ID, state.status,
                                                                           state.direction
                                                                           )
    strip = world.resource_manager.get_animation_strip(animation_identifier)

    if state.status == Status.IDLE:
        animation_frames = 1
    elif state.status.WALKING:
        animation_frames = MOVE_ANIMATION_DELAY
    elif state.status.ATTACKING:
        animation_frames = ATTACK_ANIMATION_DELAY
    else:
        raise RuntimeError(
            f'Animation frame for player not specified for the status {state.status} and direction {state.direction}'
        )

    world.add_component(ent_id, cmp.Animation.from_delay(strip, animation_frames))

# def handle_input(input_event: InputEvent, player_entity_id: int, world: zesper.World):
#     velocity = world.component_for_entity(player_entity_id, cmp.Velocity)
#     position = world.component_for_entity(player_entity_id, cmp.Position)
#
#     direction_x = - input_event.controller.is_button_down(Button.LEFT) + input_event.controller.is_button_down(
#         Button.RIGHT
#         )
#     direction_y = - input_event.controller.is_button_down(Button.UP) + input_event.controller.is_button_down(
#         Button.DOWN
#         )
#
#     abs_vel = VELOCITY_DIAGONAL if (direction_y and direction_x) else VELOCITY
#     velocity.x = direction_x * abs_vel
#     velocity.y = direction_y * abs_vel
#
#     # Snaps position to grid when the respective key has been released.  This allows for a deterministic movement
#     # pattern by eliminating any decimal residual accumulated when resetting the position to an integer value
#     horizontal_key_released = (input_event.controller.is_button_released(Button.LEFT) or
#                                input_event.controller.is_button_released(Button.RIGHT))
#     vertical_key_released = (input_event.controller.is_button_released(Button.UP) or
#                              input_event.controller.is_button_released(Button.DOWN))
#
#     if horizontal_key_released:
#         position.x = round(position.x)
#     if vertical_key_released:
#         position.y = round(position.y)
#
#     # Attempt to change direction only when a key is released or the status of the entity is not moving
#     state = world.component_for_entity(player_entity_id, cmp.State)
#     state.update()
#
#     if (
#             horizontal_key_released or vertical_key_released) or state.status != Status.WALKING:  # If it's moving don't change directions
#         if direction_x > 0:
#             state.direction = Direction.RIGHT
#         elif direction_x < 0:
#             state.direction = Direction.LEFT
#         if direction_y > 0:
#             state.direction = Direction.DOWN
#         elif direction_y < 0:
#             state.direction = Direction.UP
#
#     if not direction_x and not direction_y:
#         state.status = Status.IDLE
#     else:
#         state.status = Status.WALKING
#
#     if input_event.controller.is_button_pressed(Button.B):
#         state.status = Status.ATTACKING
#         velocity.x = 0  # Stop player when is attacking
#         velocity.y = 0
#
#         # TODO: one should create a small delay until the actual hitbox is created as the attack animation has some
#         #   of gaining momentum for the swing
#         # Creates a temporary hitbox representing the sword weapon
#         create_melee_weapon(player_entity_id, world)
#
#         # Block input until weapon lifetime is over and publish attach event. We need to block it one frame less than
#         # the number of active frames as we are counting already the frame when it is activated as active
#         sound_trigger_event = SoundTriggerEvent(SWORD_SOUND_EFFECT)
#         block_event = BlockInputEvent(SWORD_ACTIVE_FRAMES - 1)
#         world.event_queue.add(sound_trigger_event)
#         world.event_queue.add(block_event)
#
#     elif input_event.controller.is_button_pressed(Button.A):
#         create_interactive_hitbox(player_entity_id, world)
#
#     elif input_event.controller.is_button_pressed(Button.L):
#         explosion_event = ExplosionEvent(position, 30, 30, cfg.C_WHITE)
#         world.event_queue.add(explosion_event)
#
#     elif input_event.controller.is_button_pressed(Button.X):
#         drop_bomb(player_entity_id, world)
#
#     elif input_event.controller.is_button_pressed(Button.SELECT):
#         cfg.DEBUG_MODE = not cfg.DEBUG_MODE
#
#     if state.has_changed():
#         handle_animation_for_input(player_entity_id, state, world)
#
#
# def _create_hitbox_in_front(player_entity_id: int, front_range: int, side_range: int,
#                             world: zesper.World) -> cmp.HitBox:
#     """ Creates a hitbox in the direction the player is facing """
#     direction = world.component_for_entity(player_entity_id, cmp.State).direction
#     player_hitbox = world.component_for_entity(player_entity_id, cmp.HitBox)
#
#     if direction in (Direction.LEFT, Direction.RIGHT):
#         hitbox = cmp.HitBox(0, 0, front_range, side_range)
#         hitbox.x = player_hitbox.x + (
#                 (player_hitbox.w - front_range) + (player_hitbox.w + front_range) * (direction.value.x)) // 2
#         hitbox.y = player_hitbox.y + (player_hitbox.h - side_range) // 2
#     else:
#         hitbox = cmp.HitBox(0, 0, side_range, front_range)
#         hitbox.x = player_hitbox.x + (player_hitbox.w - side_range) // 2
#         hitbox.y = player_hitbox.y + (
#                 (player_hitbox.h - front_range) + (player_hitbox.h + front_range) * (direction.value.y)) // 2
#
#     return hitbox

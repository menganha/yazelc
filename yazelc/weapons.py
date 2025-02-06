from settings import C_RED
from yazelc import zesper
from yazelc.components import Renderable, Animation, Position, Weapon, HitBox
from yazelc.event.events import BombExplosionEvent, ExplosionEvent

BOMB_DAMAGE = 3
BOMB_SPRITES_ID = 'BOMB'
BOMB_SPRITE_WIDTH = 16
BOMB_FRAME_SEQUENCE = [0] * 52 + [0, 0, 1, 1, 2, 2] * 8
BOMB_ACTIVE_FRAMES = 10
BOMB_RANGE = 20
BOMB_FREEZE_FRAMES = 15
BOMB_RECOIL_VELOCITY = 2
BOMB_EXPLOSION_PARTICLES = 60
BOMB_EXPLOSION_DELAY_TIME = 100
BOMB_EXPLOSION_COLOR = C_RED


def create_bomb(position: Position, world: zesper.World):
    """ Creates the Bomb, bomb explosion event, and the visual explosion"""
    entity_id = world.create_entity()
    strip = world.resource_manager.get_animation_strip(BOMB_SPRITES_ID)
    bomb_renderable_component = Renderable(image=strip[0])
    world.add_component(entity_id, bomb_renderable_component)
    world.add_component(entity_id, Animation(strip, BOMB_FRAME_SEQUENCE))
    world.add_component(entity_id, position)

    bomb_explosion_event = BombExplosionEvent(entity_id)
    world.event_queue.add(bomb_explosion_event, BOMB_EXPLOSION_DELAY_TIME)

    x_center = position.x + BOMB_SPRITE_WIDTH // 2
    y_center = position.y + BOMB_SPRITE_WIDTH // 2

    explosion_event = ExplosionEvent((x_center, y_center), BOMB_EXPLOSION_PARTICLES, BOMB_RANGE, BOMB_EXPLOSION_COLOR)
    world.event_queue.add(explosion_event, BOMB_EXPLOSION_DELAY_TIME)


def add_weapon_component_to_bomb(bomb_entity_id: int, world: zesper.World):
    hitbox = HitBox(0, 0, BOMB_RANGE * 2, BOMB_RANGE * 2)
    position = world.component_for_entity(bomb_entity_id, Position)
    x_center = position.x + BOMB_SPRITE_WIDTH // 2
    y_center = position.y + BOMB_SPRITE_WIDTH // 2
    hitbox.center = (x_center, y_center)
    weapon_cmp = Weapon(BOMB_DAMAGE, BOMB_ACTIVE_FRAMES, BOMB_FREEZE_FRAMES, BOMB_RECOIL_VELOCITY)
    world.add_component(bomb_entity_id, weapon_cmp)
    world.add_component(bomb_entity_id, hitbox)

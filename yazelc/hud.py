import pygame

import player
import settings as cfg
from yazelc import zesper
from yazelc.components import Renderable, Position
from yazelc.utils.game_utils import IVec

WHOLE_HEART_HEALTH_POINTS = 2
HUD_DEPTH = 1001
HUD_WIDTH = cfg.RESOLUTION.x
HUD_HEIGHT = 40
FULL_HEART_RESOURCE_NAME = 'full_heart'
HALF_HEART_RESOURCE_NAME = 'half_heart'
EMPTY_HEART_RESOURCE_NAME = 'empty_heart'
HUD_FONT_ID = 'HUD'

HEART_OFFSET = IVec(2, 2)


def create_hud_entity(world: zesper.World, health_points: int) -> int:
    hud_entity_id = world.create_entity()
    world.hud_entity_id = hud_entity_id
    hud_surface = pygame.surface.Surface((HUD_WIDTH, HUD_HEIGHT), flags=pygame.SRCALPHA)
    world.add_component(hud_entity_id, Position(0, 0, absolute=True))
    world.add_component(hud_entity_id, Renderable(hud_surface, depth=HUD_DEPTH))
    update_hud_hearts(hud_entity_id, health_points, world)
    # TODO: Add here also all the updates for all the items that the hud consists of
    return hud_entity_id


def update_hud_keys(hud_entity_id: int, world: zesper.World, n_keys: int):
    hud_image = world.component_for_entity(hud_entity_id, Renderable).image
    font = world.resource_manager.get_font('HUD')
    text = f'KEYS: {n_keys}'
    rect = font.get_rect(text)
    hud_image.fill(cfg.C_YELLOW, rect)
    font.render_text_at(text, hud_image)


def update_hud_hearts(hud_entity_id: int, health_points: int, world: zesper.World):
    hud_image = world.component_for_entity(hud_entity_id, Renderable).image
    full_heart_image = world.resource_manager.get_texture(FULL_HEART_RESOURCE_NAME)
    half_heart_image = world.resource_manager.get_texture(HALF_HEART_RESOURCE_NAME)
    empty_heart_image = world.resource_manager.get_texture(EMPTY_HEART_RESOURCE_NAME)

    num_whole_hearts, num_medium_hearts = divmod(health_points, WHOLE_HEART_HEALTH_POINTS)
    index = 0
    for idx in range(num_whole_hearts):
        hud_image.blit(full_heart_image, (idx * full_heart_image.get_width() + HEART_OFFSET.x, HEART_OFFSET.y))
        index += 1
    for idx in range(num_medium_hearts):
        hud_image.blit(half_heart_image, (index * half_heart_image.get_width() + HEART_OFFSET.x, HEART_OFFSET.y))
        index += 1
    for idx in range(player.MAX_HEALTH // 2 - num_medium_hearts - num_whole_hearts):
        hud_image.blit(empty_heart_image, (index * empty_heart_image.get_width() + HEART_OFFSET.x, HEART_OFFSET.y))
        index += 1

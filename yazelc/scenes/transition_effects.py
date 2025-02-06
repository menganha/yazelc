"""
Transition effect when entering or exiting and scene
"""
from __future__ import annotations

from math import copysign
from typing import TYPE_CHECKING

import pygame

import settings as cfg
import yazelc.components as cmp
from yazelc import zesper
from yazelc.camera import Camera
from yazelc.systems.collision_system import CollisionSystem
from yazelc.systems.player_input_system import PlayerInputSystem

if TYPE_CHECKING:
    pass

TOTAL_EXIT_FRAMES = 80
CIRCLE_INITIAL_RADIUS = cfg.RESOLUTION.x - 100


def closing_circle(player_entity_id: int, camera: Camera, world: zesper.World):
    """ Enclosing circle effect """

    # Continue running through the door
    velocity = world.component_for_entity(player_entity_id, cmp.Velocity)
    hitbox = world.component_for_entity(player_entity_id, cmp.HitBox)
    position = cmp.Position(hitbox.x, hitbox.y)
    velocity.x = 0.30 * copysign(1.0, velocity.x) if abs(velocity.x) > 1e-4 else 0
    velocity.y = 0.30 * copysign(1.0, velocity.y) if abs(velocity.y) > 1e-4 else 0

    world.remove_processor(PlayerInputSystem)
    world.remove_processor(CollisionSystem)
    world.remove_processor(CameraSystem)

    effect_id = world.create_entity()
    radius = CIRCLE_INITIAL_RADIUS
    cover_surface = pygame.Surface((cfg.RESOLUTION.x, cfg.RESOLUTION.y))
    cover_surface.fill(cfg.C_BLACK)
    cover_surface.set_colorkey(cfg.C_WHITE)
    pygame.draw.circle(cover_surface, cfg.C_WHITE, (position.x - camera.pos.x, position.y - camera.pos.y), radius)
    renderable = cmp.Renderable(image=cover_surface, depth=6000)
    world.add_component(effect_id, renderable)
    world.add_component(effect_id, cmp.Position(camera.pos.x, camera.pos.y))

    frames_to_exit = TOTAL_EXIT_FRAMES
    while frames_to_exit > 0:
        world.process()
        cover_surface.fill(cfg.C_BLACK)
        pygame.draw.circle(cover_surface, cfg.C_WHITE, (position.x - camera.pos.x, position.y - camera.pos.y), radius)
        world.component_for_entity(effect_id, cmp.Renderable).image = cover_surface
        radius -= 5
        frames_to_exit -= 1

# def map_translation(current_map: Map, next_scene: GameplayScene, world: zesper.World):
#     # TODO: remove enemies
#     # TODO: add velocity depending on the direction of the player. Keep in mind potential diagonal movement
#     # TODO: Remove all enemies
#     # TODO: Are the dimensions of the map going to be the same? in that case the initial x and y of the next map should be
#     #       determined: Solution! we know already a coordinate, i.e, the initial coordinate of the player on the new map.
#     #       Make the initial coordinate of the following map player coordinate dependant
#
#     for layer_entity_id in current_map.layer_entities:
#         world.add_component(layer_entity_id, cmp.Velocity(-4, 0))
#
#     current_map = Map(next_scene.map_data_file, world.resource_manager)
#     for idx, map_layer in enumerate(current_map.get_map_images()):
#         layer_entity_id = world.create_entity()
#         world.add_component(layer_entity_id, cmp.Position(x=cfg.RESOLUTION.x, y=0))  # TODO: What if the dimensions are different
#         depth = 2000 * (idx + 1000)  # 1000 * idx # To hide player
#         world.add_component(layer_entity_id, cmp.Renderable(image=map_layer, depth=depth))
#         world.add_component(layer_entity_id, cmp.Velocity(-4, 0))
#
#     world.remove_processor(InputSystem)
#     world.remove_processor(CollisionSystem)
#     world.remove_processor(CameraSystem)
#
#     frames_to_exit = round(cfg.RESOLUTION.x / 4)
#     while frames_to_exit > 0:
#         world.process()
#         frames_to_exit -= 1

from math import copysign
from pathlib import Path
from typing import Optional, Any

import pygame

from yazelc import components as cmp
from yazelc import config as cfg
from yazelc import dialog_box
from yazelc import enemy
from yazelc import hud
from yazelc import items
from yazelc import weapons
from yazelc import zesper
from yazelc.camera import Camera
from yazelc.controller import Controller
from yazelc.event import events
from yazelc.items import CollectableItemType
from yazelc.map import Map, WorldMap
from yazelc.menu import menu_box
from yazelc.player import player
from yazelc.scenes import transition_effects
from yazelc.scenes.base_scene import BaseScene
from yazelc.systems.ai_system import AISystem
from yazelc.systems.animation_system import AnimationSystem
from yazelc.systems.camera_system import CameraSystem
from yazelc.systems.collision_system import CollisionSystem
from yazelc.systems.combat_system import CombatSystem
from yazelc.systems.delayed_entity_removal_system import EntityRemovalSystem
from yazelc.systems.dialog_menu_system import DialogMenuSystem
from yazelc.systems.hud_system import HudSystem
from yazelc.systems.inventory_system import InventorySystem
from yazelc.systems.movement_system import MovementSystem
from yazelc.systems.player_input_system import PlayerInputSystem
from yazelc.systems.render_system import RenderSystem
from yazelc.systems.sound_system import SoundSystem
from yazelc.systems.tween_system import TweenSystem
from yazelc.systems.visual_effects_system import VisualEffectsSystem
from yazelc.utils.game_utils import Direction, IVec

FULL_HEART_IMAGE_PATH = Path('assets', 'sprites', 'full_heart.png')
PLAYER_IMAGE_PATH = Path('assets', 'sprites', 'player')
HALF_HEART_IMAGE_PATH = Path('assets', 'sprites', 'half_heart.png')
EMPTY_HEART_IMAGE_PATH = Path('assets', 'sprites', 'empty_heart.png')
ENEMY_PATH = Path('assets', 'sprites', 'enemy')
COINS_IMAGE_PATH = Path('assets', 'sprites', 'coins.png')
TREASURE_IMAGE_PATH = Path('assets', 'sprites', 'treasure.png')
WEAPON_IMAGE_PATH = Path('assets', 'sprites', 'weapon')
FONT_PATH = Path('assets', 'font', 'Px437_Portfolio_6x8.ttf')
FONT_COLOR = cfg.C_WHITE
FONT_SIZE = 12
SOUND_EFFECTS_PATH = Path('assets', 'sounds')
ZERO_THRESHOLD = 1e-2
BOMB_IMG_PATH = Path('assets', 'sprites', 'bomb.png')
MAP_VELOCITY_TRANSITION = 4
PROCESSOR_PRIORITY = {system: idx + 1 for idx, system in enumerate(reversed(
    [PlayerInputSystem,
     AISystem,
     TweenSystem,
     MovementSystem,
     CollisionSystem,
     DialogMenuSystem,
     CombatSystem,
     InventorySystem,
     HudSystem,
     VisualEffectsSystem,
     CameraSystem,
     AnimationSystem,
     EntityRemovalSystem,
     SoundSystem,
     RenderSystem]))}


class GameplayScene(BaseScene):

    def __init__(self, window: pygame.Surface, controller: Controller, map_file_path: Path, start_tile_position: IVec,
                 player_components: tuple[Any, ...] = None, music_path: Path = None):
        super().__init__(window, controller)
        self.map_data_file = map_file_path
        self.start_tile_position = start_tile_position
        self.camera: Optional[Camera] = None
        self.map: Optional[Map] = None
        self.player_entity_id: Optional[int] = None
        self.music_path = music_path
        self._player_components = player_components
        self._cached_scene_processors: list[zesper.Processor] = []

    def on_enter(self):

        self._load_resources()
        self._generate_map()
        self._generate_objects()

        if self.music_path:
            pygame.mixer.music.load(self.music_path)
            pygame.mixer.music.play(-1)

        # Add player entity
        player_x_pos, player_y_pos = self.map.get_center_coord_from_tile(*self.start_tile_position)
        if self._player_components is None:
            self.player_entity_id = player.create_player_at(center_x_pos=player_x_pos, center_y_pos=player_y_pos,
                                                            world=self.world)
        else:
            self.player_entity_id = self.world.create_entity(*self._player_components)
            position = self.world.component_for_entity(self.player_entity_id, cmp.Position)
            velocity = self.world.component_for_entity(self.player_entity_id, cmp.Velocity)
            hitbox = self.world.component_for_entity(self.player_entity_id, cmp.HitBox)
            velocity.x, velocity.y = (0, 0)
            hitbox.center = (player_x_pos, player_y_pos)
            position.x, position.y = player.get_position_of_sprite(hitbox)

        # Add camera entity
        self.camera = Camera(0, 0, self.map.width, self.map.height)
        self.camera.track_entity(self.player_entity_id, self.world)

        # Initialize the HUD
        health_points = self.world.component_for_entity(self.player_entity_id, cmp.Health).points
        hud_entity_id = hud.create_hud_entity(self.world, health_points)

        # Create a pickable item
        for idx in range(3):
            x_pos, y_pos = self.map.get_center_coord_from_tile(7 + idx, 17)
            items.create_entity(CollectableItemType.COIN, x_pos, y_pos, self.world)
        # items.create_entity(items.PickableItemType.HEART, 300, 355, self.world)
        # items.create_entity(items.PickableItemType.HEART, 350, 355, self.world)
        inventory = {collectable_type: 0 for collectable_type in CollectableItemType}

        # Create the systems for the scene
        combat_system = CombatSystem(self.player_entity_id)
        inventory_system = InventorySystem(self.player_entity_id, inventory)
        input_system = PlayerInputSystem(self.player_entity_id)
        vfx_system = VisualEffectsSystem()
        entity_removal_system = EntityRemovalSystem()
        collision_system = CollisionSystem()
        hud_system = HudSystem(hud_entity_id)
        ai_system = AISystem()
        sound_system = SoundSystem()
        dialog_system = DialogMenuSystem()
        self.world.add_processor(ai_system, PROCESSOR_PRIORITY[AISystem])
        self.world.add_processor(input_system, PROCESSOR_PRIORITY[PlayerInputSystem])
        self.world.add_processor(MovementSystem(), PROCESSOR_PRIORITY[MovementSystem])
        self.world.add_processor(collision_system, PROCESSOR_PRIORITY[CollisionSystem])
        self.world.add_processor(combat_system, PROCESSOR_PRIORITY[CombatSystem])
        self.world.add_processor(inventory_system, PROCESSOR_PRIORITY[InventorySystem])
        self.world.add_processor(hud_system, PROCESSOR_PRIORITY[HudSystem])
        self.world.add_processor(vfx_system, PROCESSOR_PRIORITY[VisualEffectsSystem])
        self.world.add_processor(dialog_system, PROCESSOR_PRIORITY[DialogMenuSystem])
        self.world.add_processor(TweenSystem(), PROCESSOR_PRIORITY[TweenSystem])
        self.world.add_processor(CameraSystem(self.camera), PROCESSOR_PRIORITY[CameraSystem])
        self.world.add_processor(entity_removal_system, PROCESSOR_PRIORITY[EntityRemovalSystem])
        self.world.add_processor(AnimationSystem(), PROCESSOR_PRIORITY[AnimationSystem])
        self.world.add_processor(sound_system, PROCESSOR_PRIORITY[SoundSystem])
        self.world.add_processor(RenderSystem(self.window, self.camera), PROCESSOR_PRIORITY[RenderSystem])

        # Register events
        self.event_manager.subscribe_handler(input_system)
        self.event_manager.subscribe_handler(combat_system)
        self.event_manager.subscribe_handler(inventory_system)
        self.event_manager.subscribe_handler(vfx_system)
        self.event_manager.subscribe_handler(collision_system)
        self.event_manager.subscribe_handler(entity_removal_system)
        self.event_manager.subscribe_handler(hud_system)
        self.event_manager.subscribe_handler(ai_system)
        self.event_manager.subscribe_handler(sound_system)
        self.event_manager.subscribe_handler(dialog_system)
        self.event_manager.subscribe_handler_method(events.DeathEvent, self.on_death)
        self.event_manager.subscribe_handler_method(events.HitDoorEvent, self.on_hit_door)
        self.event_manager.subscribe_handler_method(events.RestartEvent, self.on_restart)
        self.event_manager.subscribe_handler_method(events.PauseEvent, self.on_pause)
        self.event_manager.subscribe_handler_method(events.ResumeEvent, self.on_resume)

    def _load_resources(self):
        """ Should load all resources for a given scene """
        # TODO: Do not use the resource manager instance reference  within the world instance but the one on this parent node
        world_map = WorldMap.from_map_file_path(self.map_data_file)
        for tileset_image_path in world_map.get_needed_images_path():
            # We load all the resources for all maps in the particular world
            self.world.resource_manager.add_texture(tileset_image_path)
        self.world.resource_manager.add_font(FONT_PATH, FONT_SIZE, FONT_COLOR, dialog_box.DIALOG_FONT_ID)
        self.world.resource_manager.add_font(FONT_PATH, FONT_SIZE, FONT_COLOR, menu_box.MENU_FONT_ID)
        self.world.resource_manager.add_texture(FULL_HEART_IMAGE_PATH)
        self.world.resource_manager.add_texture(HALF_HEART_IMAGE_PATH)
        self.world.resource_manager.add_texture(EMPTY_HEART_IMAGE_PATH)
        self.world.resource_manager.add_animation_strip(TREASURE_IMAGE_PATH, InventorySystem.TREASURE_TILE_SIZE,
                                                        explicit_name=InventorySystem.TREASURE_TEXTURE_ID)
        self.world.resource_manager.add_animation_strip(COINS_IMAGE_PATH, items.COIN_TILE_SIZE,
                                                        explicit_name=CollectableItemType.COIN.name)
        self.world.resource_manager.add_animation_strip(BOMB_IMG_PATH, weapons.BOMB_SPRITE_WIDTH,
                                                        explicit_name=weapons.BOMB_SPRITES_ID)
        for path in SOUND_EFFECTS_PATH.glob(f'*{self.resource_manager.OGG_FILETYPE}'):
            self.world.resource_manager.add_sound(path)

        self.world.resource_manager.add_all_animation_strips(ENEMY_PATH, enemy.KEFER_ID, enemy.KEFER_SPRITE_WIDTH)
        self.world.resource_manager.add_all_animation_strips(PLAYER_IMAGE_PATH, player.SPRITE_SHEET_ID,
                                                             player.SPRITE_SIZE)
        self.world.resource_manager.add_all_animation_strips(ENEMY_PATH, enemy.JELLY_ID, enemy.JELLY_SPRITE_WIDTH)

        # idle animation
        for direction in [Direction.UP, Direction.DOWN, Direction.RIGHT, Direction.LEFT]:
            identifier = f'wooden_sword_{direction.name}'
            img_path = WEAPON_IMAGE_PATH / f'{identifier}.png'.lower()
            flip = False
            if direction == Direction.LEFT:
                flip = True
                img_path = WEAPON_IMAGE_PATH / f'wooden_sword_{Direction.RIGHT.name}.png'.lower()
            self.world.resource_manager.add_animation_strip(img_path, player.SWORD_SPRITE_WIDTH, flip, identifier)

    def _generate_map(self, x_pos: int = 0, y_pos: int = 0):
        """
        Generates the map with all the relevant data, e.g., items, enemies, triggers, etc.
        """

        self.map = Map(self.map_data_file, self.world.resource_manager)

        for depth, map_layer in self.map.get_map_images():
            layer_entity_id = self.world.create_entity()
            self.world.add_component(layer_entity_id, cmp.Position(x=x_pos, y=y_pos))
            self.world.add_component(layer_entity_id, cmp.Renderable(image=map_layer, depth=depth))
            self.map.layer_entities.append(layer_entity_id)

    def _generate_objects(self):
        dialog_font = self.world.resource_manager.get_font(dialog_box.DIALOG_FONT_ID)
        for components in self.map.create_colliders():
            ent_id = self.world.create_entity(*components)
            self.map.object_entities.append(ent_id)
        for components in self.map.create_interactive_objects(dialog_font):
            ent_id = self.world.create_entity(*components)
            self.map.object_entities.append(ent_id)
        for door, hitbox in self.map.create_doors():
            ent_id = self.world.create_entity(door, hitbox)
            self.map.object_entities.append(ent_id)
        for pos_x, pos_y, enemy_type in self.map.create_enemies():
            ent_id = enemy.create_enemy_at(pos_x, pos_y, self.world,
                                           enemy_type)  # TODO: Generalize for any type of enemy
            self.map.object_entities.append(ent_id)

    def on_exit(self):
        if type(self.next_scene) == type(self) and self.next_scene != self:  # Why do we make this check?
            transition_effects.closing_circle(self.player_entity_id, self.camera, self.world)
        pygame.mixer.music.fadeout(20)

    def on_pause(self, _pause_event: events.PauseEvent):
        """
        Removes all control form other entities unless it has a dialog or menu component
        We store these components locally for later reinsertion
        """

        input_processor = self.world.get_processor(PlayerInputSystem)
        self.event_manager.remove_handler(input_processor)
        self._cached_scene_processors = self.world.remove_all_processors_except(RenderSystem, DialogMenuSystem)

    def on_resume(self, _resume_event: events.ResumeEvent):
        for proc in self._cached_scene_processors:
            self.world.add_processor(proc, PROCESSOR_PRIORITY[type(proc)])
        input_processor = self.world.get_processor(PlayerInputSystem)
        self.event_manager.subscribe_handler(input_processor)
        self._cached_scene_processors = []

    def on_restart(self, _restart_event: events.RestartEvent):
        self.finished = True
        self.next_scene = self
        self.player_entity_id = None  # TODO: Should one keep the player or store some information here?
        self.world.clear_database()
        self.event_manager.remove_all_handlers()
        self.event_queue.clear()

    def on_hit_door(self, hit_door_event: events.HitDoorEvent):
        if hit_door_event.transversing_entity != self.player_entity_id:  # Only player can go through door
            return
        door = self.world.component_for_entity(hit_door_event.door_entity, cmp.Door)

        if door.target_map.parent != self.map_data_file.parent:  # If it is not part of the same parent map, i.e., another world
            self.finished = True
            player_components = self.world.components_for_entity(self.player_entity_id)
            current_scene_class = type(self)  # NOTE: It may be other type of scenes
            non_overworld_music_path = Path('assets', 'music', 'Los_Miticos_del_Ritmo-La_Libanessa.ogg')
            self.next_scene = current_scene_class(self.window, self.controller, door.target_map,
                                                  IVec(door.target_x, door.target_y),
                                                  player_components, non_overworld_music_path)
        else:
            self.event_queue.clear()

            # Delete object entities and store references to old map layer image entities for generating the "scroll" effect
            for ent_id in self.map.object_entities:
                if self.world.entity_exists(ent_id):
                    self.world.delete_entity(ent_id)
            previous_map_layers = self.map.layer_entities

            player_position = self.world.component_for_entity(self.player_entity_id, cmp.Position)
            player_hitbox = self.world.component_for_entity(self.player_entity_id, cmp.HitBox)
            player_velocity = self.world.component_for_entity(self.player_entity_id, cmp.Velocity)

            # player_position.x, player_position.y = self.maps.get_coord_from_tile(door.target_x, door.target_y)
            # player_hitbox.rect.centerx, player_hitbox.rect.centery = player.get_position_of_hitbox(player_position)

            normal = [0 if abs(value) < ZERO_THRESHOLD else copysign(1, value) for value in
                      (player_velocity.x, player_velocity.y)]
            map_velocity = [- value * MAP_VELOCITY_TRANSITION for value in normal]
            new_map_position = [nor * res for (nor, res) in zip(normal, cfg.RESOLUTION)]

            # Generate new map and add velocity to the map layers and player
            self.map_data_file = door.target_map
            self._generate_map(*new_map_position)

            for layer_entity_id in self.map.layer_entities:
                self.world.add_component(layer_entity_id, cmp.Velocity(*map_velocity))
            for layer_entity_id in previous_map_layers:
                self.world.add_component(layer_entity_id, cmp.Velocity(*map_velocity))

            # Store some processors and remove them temporarily
            # TODO: Remove input handlers

            for processor_type in (CollisionSystem, CameraSystem):
                proc = self.world.get_processor(processor_type)
                self._cached_scene_processors.append(proc)
                self.world.remove_processor(processor_type)

            # Run the animation. Remove magic numbers
            distance = (cfg.RESOLUTION.x if abs(normal[0]) > ZERO_THRESHOLD else cfg.RESOLUTION.y)
            frames_to_exit = round(distance / MAP_VELOCITY_TRANSITION)
            # TODO: The amount of tiles is variable. For example for transitions without doors it , e.g., 1.2 instead of 3
            velocity_for_three_tiles = [map_vel + 3 * cfg.TILE_WIDTH * nor / frames_to_exit for (map_vel, nor) in
                                        zip(map_velocity, normal)]
            player_velocity.x, player_velocity.y = velocity_for_three_tiles
            while frames_to_exit > 0:
                self.world.process()
                frames_to_exit -= 1

            player_velocity.x, player_velocity.y = 0, 0
            player_position.x, player_position.y = self.map.get_coord_from_tile(door.target_x, door.target_y)
            player_hitbox.centerx, player_hitbox.centery = player.get_position_of_hitbox(player_position)

            # Remove velocity components and delete old map layer entities
            for layer_entity_id in self.map.layer_entities:
                self.world.remove_component(layer_entity_id, cmp.Velocity)
            for layer_entity_id in previous_map_layers:
                self.world.delete_entity(layer_entity_id)

            # Generate new objects and add the cached processors
            self._generate_objects()
            for proc in self._cached_scene_processors:
                self.world.add_processor(proc, PROCESSOR_PRIORITY[type(proc)])
            self._cached_scene_processors = []

    def on_death(self, _death_event: events.DeathEvent):
        """
        Saves the status of the player (weapons, hearts, etc., wherever that is allocated in the end), removes all processors
        except the animation and render processor, and creates a death menu
        """
        menu_box.create_death_menu(self.world)

        self.world.remove_all_processors_except(RenderSystem)

        input_processor = self.world.get_processor(PlayerInputSystem)
        self.event_manager.remove_handler(input_processor)
        self._cached_scene_processors = self.world.remove_all_processors_except(RenderSystem)

        dialog_system = DialogMenuSystem()
        self.world.add_processor(dialog_system)
        self.event_manager.subscribe_handler(dialog_system)

        # for entity_id in self.world.map_layers_entity_id:
        #     self.world.delete_entity(entity_id)

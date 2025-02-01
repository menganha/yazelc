"""
Module deals with map data
"""
import json
import logging
import os.path
from pathlib import Path
from typing import Iterator, Optional
from xml.etree import ElementTree

import pygame
from pytmx import TiledTileLayer, TiledMap, util_pygame

from yazelc import components as cmp
from yazelc.items import CollectableItemType
from yazelc.resource_manager import ResourceManager


class WorldMap:
    WORLD_MAP_SUFFIX = '.world'

    def __init__(self, world_map_file_path: Path):
        self.file_path = world_map_file_path
        with open(self.file_path) as file:
            self._data = json.load(file)

    def get_needed_images_path(self) -> list[Path]:
        """ Gets the filepaths of all the tilesets used for the maps of this world """
        image_paths = []
        for single_map in self._data['maps']:
            file_name = single_map['fileName']
            file_path = Path(self.file_path.parent, file_name)
            tree = ElementTree.parse(file_path)
            for node in tree.findall('.//tileset'):
                relative_path = node.get('source')
                tileset_path = Path(self.file_path.parent, relative_path)
                tileset_tree = ElementTree.parse(tileset_path)
                for tileset_node in tileset_tree.findall('.//image'):
                    image_relative_path = tileset_node.get('source')
                    image_path = Path(tileset_path.parent, image_relative_path)
                    image_paths.append(image_path)
        return image_paths

    @staticmethod
    def get_world_map_file_path(map_file_path: Path) -> Path:
        list_world_map_files = list(map_file_path.parent.glob(f'*{WorldMap.WORLD_MAP_SUFFIX}'))
        if len(list_world_map_files) != 1:
            raise RuntimeError(f'None or more than one world file on the folder {map_file_path.parent}')
        return list_world_map_files[0]

    @classmethod
    def from_map_file_path(cls, map_file_path: Path) -> 'WorldMap':
        """ Derives from a map file (.tmx) the world map"""
        world_map_file_path = cls.get_world_map_file_path(map_file_path)
        return cls(world_map_file_path)


class Map:
    """
    Loads ands stores all map entities from a TMX file

    It joins the different tiles surfaces to generate a single image map

    A tile layer with the name "foreground" has n special meaning. No colliders will be instantiated for it, and it
    will generate it own image map that will be overlaid on top of all others. This is to show 3d depth by hiding
    the character in between these two layers, e.g., in between trees

    """
    DOOR_TARGET_X_STR = 'target_x'
    DOOR_TARGET_Y_STR = 'target_y'
    DOOR_TARGET_STR = 'target_door'
    DOOR_PATH_SEP = ':'
    FOREGROUND_LAYER_NAME = 'foreground'
    ENEMY_PROPERTY = 'enemy'
    COLLIDER_PROPERTY = 'colliders'
    TEXT_PROPERTY = 'text'
    ITEM_PROPERTY = 'item'
    FOREGROUND_LAYER_DEPTH = 1000
    GROUND_LEVEL_DEPTH = 0

    def __init__(self, map_file_path: Path, resource_manager: ResourceManager):
        self.map_file_path = map_file_path
        self.resource_manager = resource_manager
        self.tmx_data = TiledMap(str(map_file_path), image_loader=self.yazelc_tiled_image_loader)
        self.width = self.tmx_data.width * self.tmx_data.tilewidth
        self.height = self.tmx_data.height * self.tmx_data.tileheight

        self.layer_entities = []  # TODO: Maybe remove this away and put it in some other container
        self.object_entities = []

    def get_map_images(self) -> list[tuple[int, pygame.Surface]]:
        """
        Generate the current map surface. We usually have two: A background and a foreground that is drawn on
        to of all the sprites
        """
        map_width = self.tmx_data.width * self.tmx_data.tilewidth
        map_height = self.tmx_data.height * self.tmx_data.tileheight

        map_image = pygame.Surface((map_width, map_height), flags=pygame.SRCALPHA)
        for layer in self.tmx_data.layers:
            if layer.name == self.FOREGROUND_LAYER_NAME or not isinstance(layer, TiledTileLayer):
                continue
            for x, y, image, in layer.tiles():
                map_image.blit(image, (x * self.tmx_data.tilewidth, y * self.tmx_data.tileheight))

        if self.FOREGROUND_LAYER_NAME in map(lambda name: name.lower(), self.tmx_data.layernames):
            map_foreground_image = pygame.Surface((map_width, map_height), flags=pygame.SRCALPHA)
            foreground_layer = self.tmx_data.get_layer_by_name(self.FOREGROUND_LAYER_NAME)
            for x, y, image, in foreground_layer.tiles():
                map_foreground_image.blit(image, (x * self.tmx_data.tilewidth, y * self.tmx_data.tileheight))
            return [(self.GROUND_LEVEL_DEPTH, map_image), (self.FOREGROUND_LAYER_DEPTH, map_foreground_image)]
        else:
            logging.debug(
                f'No foreground layer named {self.FOREGROUND_LAYER_NAME} found for the map {self.map_file_path}')
            return [(self.GROUND_LEVEL_DEPTH, map_image)]

    def create_colliders(self) -> Iterator[tuple]:
        """
        Generates the static colliders of the map based on the "collider" property of the tileset. We ignore the
        FOREGROUND layer collider.
        """
        for layer_no, layer in enumerate(self.tmx_data.layers):
            if layer.name.lower() == self.FOREGROUND_LAYER_NAME:
                continue
            if isinstance(layer, TiledTileLayer):
                for x, y, _, in layer.tiles():
                    properties = self.tmx_data.get_tile_properties(x, y, layer_no)
                    if properties and 'colliders' in properties:
                        collider = properties[self.COLLIDER_PROPERTY][0]  # Assume tile has a single collider box
                        hit_box = cmp.HitBox(x * self.tmx_data.tilewidth + collider.x,
                                             y * self.tmx_data.tileheight + collider.y, collider.width, collider.height,
                                             solid=True
                                             )
                        yield (hit_box,)

    def create_objects(self) -> Iterator[list]:
        """
        Create objects such as door, switches, chests, etc.
        """
        for obj in self.tmx_data.objects:
            components = []

            if self.COLLIDER_PROPERTY in obj.properties:
                collider = obj.properties['colliders'][0]  # Assume tile has a single collider box
                hit_box = cmp.HitBox(obj.x + collider.x, obj.y + collider.y,
                                     collider.width, collider.height,
                                     solid=True
                                     )
                components.append(hit_box)

            if obj.image:
                renderable = cmp.Renderable(obj.image)
                position = cmp.Position(obj.x, obj.y)
                components.append(renderable)
                components.append(position)

            # Mutually exclusive properties
            if self.TEXT_PROPERTY in obj.properties:
                if obj.properties[self.TEXT_PROPERTY] is None:
                    logging.error(f'Sign with id {obj.id} has no dialog')
                dialog = cmp.Sign(obj.properties[self.TEXT_PROPERTY])
                components.append(dialog)

            elif self.ITEM_PROPERTY in obj.properties:
                collectable = cmp.Collectable(CollectableItemType(obj.properties[self.ITEM_PROPERTY]), 1, in_chest=True)
                components.append(collectable)

            if not components:
                logging.error(f'No parseable properties found for object with id {obj.id} and gid {obj.gid}')

            yield components

    def create_enemies(self) -> Iterator[tuple]:
        for obj in self.tmx_data.objects:
            if self.ENEMY_PROPERTY in obj.properties:
                x_pos = obj.x
                y_pos = obj.y
                enemy_type = obj.properties[self.ENEMY_PROPERTY]
                yield x_pos, y_pos, enemy_type

    def get_center_coord_from_tile(self, tile_x_pos: int, tile_y_pos: int) -> (int, int):
        """
        Get tile center absolute coordinates from the position in "tile" coordinates, i.e. the one independent of the tile size
        """
        center_x = tile_x_pos * self.tmx_data.tilewidth + int(self.tmx_data.tilewidth / 2)
        center_y = tile_y_pos * self.tmx_data.tilewidth + int(self.tmx_data.tileheight / 2)
        return center_x, center_y

    def get_coord_from_tile(self, tile_x_pos: int, tile_y_pos: int) -> (int, int):
        pos_x = tile_x_pos * self.tmx_data.tilewidth
        pos_y = tile_y_pos * self.tmx_data.tilewidth
        return pos_x, pos_y

    def yazelc_tiled_image_loader(self, filename: str, color_key: Optional[util_pygame.ColorLike], **kwargs):
        """
        pytmx image loader for pygame

        Parameters:
            filename: filename, including path, to load
            color_key: color_key for the image

        Returns:
            function to load tile images

        This is a direct copy of "pygame_image_loader" but retrieving the pygame Surfaces from the resource manager
        """
        if color_key:
            color_key = pygame.Color("#{0}".format(color_key))

        pixelalpha = kwargs.get("pixelalpha", True)
        basename_no_ext = os.path.splitext(os.path.basename(filename))[0]
        image = self.resource_manager.get_texture(basename_no_ext)

        def load_image(rect=None, flags=None):
            if rect:
                try:
                    tile = image.subsurface(rect)
                except ValueError:
                    util_pygame.logger.error("Tile bounds outside bounds of tileset image")
                    raise
            else:
                tile = image.copy()

            if flags:
                tile = util_pygame.handle_transformation(tile, flags)

            tile = util_pygame.smart_convert(tile, color_key, pixelalpha)
            return tile

        return load_image

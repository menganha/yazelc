import unittest

import pygame

pygame.init()
pygame.freetype.init()

from yazelc.map import WorldMap
from pathlib import Path


class TestMap(unittest.TestCase):
    TEST_WORLD = Path('../../data/overworld/overworld.world')
    TEST_MAP = Path('../../data/overworld/overworld_1.tmx')

    def setUp(self) -> None:
        self.world_map = WorldMap(self.TEST_WORLD)

    def test_get_world_map_file_path(self):
        world_map_path = WorldMap.get_world_map_file_path(self.TEST_MAP)
        self.assertEqual(world_map_path, self.TEST_WORLD)

    def test_from_map_file(self):
        world_map = WorldMap.from_map_file_path(self.TEST_MAP)
        self.assertEqual(world_map.file_path, self.world_map.file_path)
        self.assertEqual(world_map._data, self.world_map._data)

    def test_get_needed_images_path(self):
        image_paths = self.world_map.get_needed_images_path()
        resolved_image_paths = [path.resolve() for path in image_paths]
        expected_image_paths = [
            Path('../../assets/sprites/map/overworld.png').resolve(),
            Path('../../assets/sprites/map/books_and_treasures.png').resolve(),
        ]
        self.assertCountEqual(resolved_image_paths, expected_image_paths)

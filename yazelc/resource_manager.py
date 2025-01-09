import logging
import os.path
from pathlib import Path

import pygame
import pygame.freetype

from yazelc import animation
from yazelc.font import Font
from yazelc.utils.game_utils import Direction, Status


class ResourceManager:
    TRUE_TYPE_FONT_FILETYPE = '.ttf'
    PNG_FILETYPE = '.png'
    OGG_FILETYPE = '.ogg'

    def __init__(self, resource_root_path: str):
        """ The resources should be all under the input resource path"""
        self.resource_root_path = resource_root_path
        self._textures = {}
        self._animation_stripes = {}
        self._fonts = {}
        self._sounds = {}

    def add(self, resource_file: str):
        matching_paths = list(Path(self.resource_root_path).glob(f'**/{Path(resource_file)}', recurse_symlinks=True))
        if matching_paths:
            if len(matching_paths) > 1:
                raise ValueError(f'More than one file found for the resource: {matching_paths}')
            path = matching_paths[0]
            if path.is_file():
                if path.suffix == self.PNG_FILETYPE:
                    self.add_texture(path)
                elif path.suffix == self.OGG_FILETYPE:
                    self.add_sound(path)
                elif path.suffix == self.TRUE_TYPE_FONT_FILETYPE:
                    self.add_font(path)
                else:
                    raise ValueError(f'Unsupported resource filetype: {path}')
        else:
            raise ValueError(f'File "{resource_file}" not found under {self.resource_root_path}')

    def get(self, resource_file: str):
        ext = os.path.splitext(resource_file)[-1]
        try:
            if ext == self.PNG_FILETYPE:
                return self._textures[resource_file]
            elif ext == self.OGG_FILETYPE:
                return self._sounds[resource_file]
            elif ext == self.TRUE_TYPE_FONT_FILETYPE:
                return self._fonts[resource_file]
        except KeyError:
            raise ValueError(f'Resource for file {resource_file} was not found')

    def add_texture(self, path: Path) -> pygame.Surface:
        """ Uses file name stem if explicit name is not passed """
        if path.name not in self._textures:
            texture = pygame.image.load(path).convert_alpha()
            self._textures.update({path.name: texture})
            return texture
        else:
            logging.info(f'Image on {path} has been already loaded')
            return self._textures[path.name]

    def add_sound(self, path: Path) -> pygame.mixer.Sound:
        """ Uses file name stem if explicit name is not passed """
        if path.name not in self._sounds:
            sound = pygame.mixer.Sound(path)
            self._sounds.update({path.name: sound})
            return sound
        else:
            logging.info(f'Sound on {path} has been already loaded')
            return self._sounds[path.name]

    def add_font(self, path: Path) -> Font:
        """
        Pygame's font objects are expensive to load. If we want to instantiate the same wrapper font instance
        with, e.g, different colors and sizes, then they will use the same reference to the pygame's freetype font
        """
        if path not in self._fonts:
            font = pygame.freetype.Font(path)
            font.origin = True
            self._fonts.update({path.name: font})
            return font
        else:
            logging.info(f'Font on {path} has been already loaded')
            return self._pygame_font_objects[path.name]

    def add_animation_strip(self, path: Path, sprite_width: int, flip: bool = False, explicit_name: str = None) -> list[pygame.Surface]:
        """
        Assumes the passed image is a series of sprites depicting an animation, each with a width of <sprite_width>
        and ordered from left to right
        """
        texture = self.add_texture(path, explicit_name)
        name = path.stem if not explicit_name else explicit_name
        if name not in self._animation_stripes:
            strip = animation.get_frames_from_strip(texture, sprite_width)
            if flip:
                strip = animation.flip_strip_sprites(strip)
            self._animation_stripes.update({name: strip})
            return strip

    def add_animation_alias(self, name: str, alias: str):
        animation_strip = self.get_animation_strip(name)
        self._animation_stripes.update({alias: animation_strip})

    def get_texture(self, name: str) -> pygame.Surface:
        return self._textures[name]

    def get_font(self, name: str) -> Font:
        return self._fonts[name]

    def get_sound(self, name: str) -> pygame.mixer.Sound:
        return self._sounds[name]

    def get_animation_strip(self, name: str) -> list[pygame.Surface]:
        return self._animation_stripes[name]

    @staticmethod
    def get_animation_identifier(name_id: str, status: Status, direction: Direction = None) -> str:
        if direction:
            return f'{name_id}_{status.name}_{direction.name}'.lower()
        else:
            return f'{name_id}_{status.name}'.lower()

    def add_all_animation_strips(self, file_path: Path, name: str, sprite_width: int):
        """
        Expects file in the format name_<status>_<direction>.png and stores them in the name_<status>_<direction>. This is useful for
        moving characters (and possibly items) in the four directions.
        """

        for direction in (Direction.UP, Direction.DOWN, Direction.RIGHT, Direction.LEFT):
            flip = True if direction == Direction.LEFT else False
            direction_resource = Direction.RIGHT if direction == Direction.LEFT else direction
            for status in Status:
                identifier = self.get_animation_identifier(name, status, direction)
                img_path = file_path / (self.get_animation_identifier(name, status, direction_resource) + '.png')

                if not img_path.exists():
                    logging.info(f'The requested path for the animation strip {img_path} does not exists. Trying alternative...')
                    img_path = file_path / (self.get_animation_identifier(name, status) + '.png')
                    if not img_path.exists():
                        continue

                self.add_animation_strip(img_path, sprite_width, flip, identifier)

        # If no idle then use the first frame of the walking animation as a temporary solution
        has_idle = False
        for direction in (Direction.UP, Direction.DOWN, Direction.RIGHT, Direction.LEFT):
            status = Status.IDLE
            identifier = self.get_animation_identifier(name, status, direction)
            if identifier not in self._animation_stripes:
                walking_animation_id = self.get_animation_identifier(name, Status.WALKING, direction)
                if walking_animation_id not in self._animation_stripes:
                    continue
                strip = self.get_animation_strip(walking_animation_id)
                logging.info(f'No idle animation found for direction {direction.name}. '
                             f'Using the first frame of walking animation to replace it {walking_animation_id}')
                self._animation_stripes.update({identifier: strip[:1]})
                has_idle = True
            else:
                has_idle = True

        if not has_idle:
            logging.error(f'Could not get a replacement idle animation for animation {name} in {file_path}')

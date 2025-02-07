import json
import logging
import os.path
from pathlib import Path

import pygame

from yazelc.animation import AnimationData, EntityState, EntityDirection, AnimationSequence
from yazelc.font import Font
from yazelc.utils.game_utils import IVec

logger = logging.getLogger(__name__)


class ResourceManager:
    TRUE_TYPE_FONT_FILETYPE = '.ttf'
    PNG_FILETYPE = '.png'
    OGG_FILETYPE = '.ogg'

    def __init__(self, resource_root_path: str = ''):
        self.resource_root_path = resource_root_path
        self._images: dict[str, pygame.Surface] = {}
        self._fonts: dict[str, Font] = {}
        self._pygame_fonts: dict[str, pygame.font.Font] = {}
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._animations: dict[str, AnimationData] = {}

    def image(self, file_path: str):
        """ Loads it and stores it on the cache labeled with the file name"""
        resolved_path = os.path.abspath(os.path.join(self.resource_root_path, file_path))
        if resolved_path not in self._images:
            image = self.load_image(resolved_path)
            self._images[resolved_path] = image
        else:
            image = self._images[resolved_path]
        return image

    def sound(self, file_path: str):
        """ Loads it and stores it on the cache labeled with the file name"""
        resolved_path = os.path.abspath(os.path.join(self.resource_root_path, file_path))
        if resolved_path not in self._sounds:
            sound = self.load_sound(resolved_path)
            self._sounds[resolved_path] = sound
        else:
            sound = self._images[resolved_path]
        return sound

    def font(self, file_path: str, color: pygame.Color, size: int = 0) -> Font:
        """ Loads it and stores it on the cache with the color and size information """
        resolved_path = os.path.abspath(os.path.join(self.resource_root_path, file_path))
        name_hash = f'{file_path}_{color.r}_{color.g}_{color.b}_{color.a}_{size}'
        if name_hash not in self._fonts:
            ext = os.path.splitext(resolved_path)[-1]
            if ext.lower() == self.PNG_FILETYPE:
                image = self.image(resolved_path)
                font = Font.from_surface(image, color)
                self._fonts[name_hash] = font
            elif ext.lower() == self.TRUE_TYPE_FONT_FILETYPE:
                path = os.path.realpath(os.path.join(self.resource_root_path, resolved_path))
                pygame_name_hash = f'{resolved_path}_{size}'
                if pygame_name_hash not in self._pygame_fonts:
                    logger.info(f'Loading pygame font on {path}')
                    if size == 0:
                        logger.warning(f'Setting a size of zero for font {resolved_path}')
                    pygame_font = pygame.font.Font(path, size=size)
                    self._pygame_fonts[pygame_name_hash] = pygame_font
                else:
                    pygame_font = self._pygame_fonts[pygame_name_hash]
                font = Font.from_font(pygame_font, color)
                self._fonts[name_hash] = font
            else:
                raise ValueError(f'Unknown file extension for a font: {resolved_path}')

        else:
            font = self._fonts[name_hash]

        return font

    def animation(self, file_path: str):

        resolved_path = os.path.abspath(os.path.join(self.resource_root_path, file_path))
        if resolved_path in self._animations:
            animation_data = self._animations[resolved_path]
        else:
            logger.info(f'Loading animation data from {resolved_path}')
            with open(resolved_path) as read_file:
                data_dictionary = json.load(read_file)

            sprite_sheet = self.image(data_dictionary['sprite_sheet'])
            sprite_size = IVec(*data_dictionary['sprite_size'])
            data_dictionary['sprite_size'] = sprite_size

            all_animation_sequences = dict()
            for seq in data_dictionary['sequences']:
                state, direction = seq.split('_', maxsplit=1)
                key = EntityState[state.upper()], EntityDirection[direction.upper()]

                repeat = data_dictionary['sequences'][seq]['repeat']
                all_frames = data_dictionary['sequences'][seq]['frames']

                hashes = []
                for *frame, duration in all_frames:
                    id_name = f"{str(frame[0])}_{str(frame[1])}_{os.path.basename(data_dictionary['sprite_sheet'])}__"
                    img_hash = os.path.abspath(os.path.join(self.resource_root_path, id_name))
                    if img_hash not in self._images:
                        clipping_rect = pygame.Rect(
                            frame[1] * sprite_size.x, frame[0] * sprite_size.y, sprite_size.x, sprite_size.y
                        )
                        image = sprite_sheet.subsurface(clipping_rect)
                        self._images[img_hash] = image
                    hashes.extend([img_hash] * duration)

                all_animation_sequences[key] = AnimationSequence(hashes, repeat)

                # Add right animations inverted and in reverse order
                if key[1] == EntityDirection.RIGHT:
                    inverted_key = key[0], EntityDirection.LEFT
                    new_hashes = []
                    for img_hash in hashes:
                        new_img_hash = f'{img_hash}inverted'
                        if new_img_hash not in self._images:
                            img = self._images[img_hash]
                            new_img = pygame.transform.flip(img, flip_x=True, flip_y=False)
                            self._images[new_img_hash] = new_img
                        new_hashes.append(new_img_hash)

                    all_animation_sequences[inverted_key] = AnimationSequence(new_hashes, repeat)

            data_dictionary['sequences'] = all_animation_sequences
            animation_data = AnimationData(**data_dictionary)
            self._animations[resolved_path] = animation_data

        return animation_data

    def find_file(self, file_name: str) -> str:
        matching_paths = list(Path(self.resource_root_path).glob(f'**/{Path(file_name)}', recurse_symlinks=True))
        if matching_paths and len(matching_paths) == 1:
            return str(matching_paths[0].absolute())
        else:
            if not matching_paths:
                raise ValueError(f'File {file_name} not found on {os.path.abspath(self.resource_root_path)}')
            else:
                raise ValueError(f'More than one file found for the same resource name: {matching_paths}')

    @staticmethod
    def get_user_path(application_name: str) -> str:
        """ Gets user path to store things like save data, etc."""
        if os.name == 'posix':
            folder = os.path.join(os.getenv('HOME'), '.local', 'share', application_name)
            os.makedirs(folder, exist_ok=True)
            return application_name
        else:
            raise NotImplementedError(f'Storing save data is not implemented for the system {os.name}')

    @staticmethod
    def load_image(path: str) -> pygame.Surface:
        logger.info(f'Loading image on {path}')
        image = pygame.image.load(path).convert_alpha()
        return image

    @staticmethod
    def load_sound(path: str) -> pygame.mixer.Sound:
        logger.info(f'Loading sound on {path}')
        sound = pygame.mixer.Sound(path)
        return sound

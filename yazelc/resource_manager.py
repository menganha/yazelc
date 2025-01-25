import json
import logging
import os.path
from pathlib import Path

import pygame

from yazelc.animation import AnimationData, AnimationState, AnimationDirection, AnimationSequence
from yazelc.font import Font
from yazelc.utils.game_utils import IVec

logger = logging.getLogger(__name__)


class ResourceManager:
    TRUE_TYPE_FONT_FILETYPE = '.ttf'
    PNG_FILETYPE = '.png'
    OGG_FILETYPE = '.ogg'

    def __init__(self, resource_root_path: str = None):
        """ The resources should be all under the resource path"""
        self.resource_root_path = resource_root_path or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._images: dict[str, pygame.Surface] = {}
        self._fonts: dict[str, Font] = {}
        self._pygame_fonts: dict[str, pygame.font.Font] = {}
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._animations: dict[str, AnimationData] = {}

    def image(self, file_name: str):
        """ Loads it and stores it on the cache labeled with the file name"""
        if file_name not in self._images:
            path = self._get_matching_paths(file_name)
            image = ResourceManager.load_image(path)
            self._images[file_name] = image
        else:
            image = self._images[file_name]
        return image

    def sound(self, file_name: str):
        """ Loads it and stores it on the cache labeled with the file name"""
        if file_name not in self._sounds:
            path = self._get_matching_paths(file_name)
            sound = self.load_sound(path)
            self._sounds[file_name] = sound
        else:
            sound = self._images[file_name]
        return sound

    def font(self, file_name: str, color: pygame.Color, size: int = 0) -> Font:
        """ Loads it and stores it on the cache with the color and size information """
        name_hash = f'{file_name}_{color.r}_{color.g}_{color.b}_{color.a}_{size}'
        if name_hash not in self._fonts:
            ext = os.path.splitext(file_name)[-1]
            if ext.lower() == self.PNG_FILETYPE:
                image = self.image(file_name)
                font = Font.from_surface(image, color)
                self._fonts[name_hash] = font
            elif ext.lower() == self.TRUE_TYPE_FONT_FILETYPE:
                path = self._get_matching_paths(file_name)
                pygame_name_hash = f'{file_name}_{size}'
                if pygame_name_hash not in self._pygame_fonts:
                    logger.info(f'Loading pygame font on {path}')
                    if size == 0:
                        logger.warning(f'Setting a size of zero for font {file_name}')
                    pygame_font = pygame.font.Font(path, size=size)
                    self._pygame_fonts[pygame_name_hash] = pygame_font
                else:
                    pygame_font = self._pygame_fonts[pygame_name_hash]
                font = Font.from_font(pygame_font, color)
                self._fonts[name_hash] = font
            else:
                raise ValueError(f'Unknown file extension for a font: {file_name}')

        else:
            font = self._fonts[name_hash]

        return font

    def animation(self, file_name: str):

        if file_name in self._animations:
            animation_data = self._animations[file_name]
        else:
            path = self._get_matching_paths(file_name)
            logger.info(f'Loading animation data from {path}')
            with open(path) as read_file:
                data_dictionary = json.load(read_file)

            sprite_sheet = self.image(os.path.basename(data_dictionary['sprite_sheet']))
            sprite_size = IVec(*data_dictionary['sprite_size'])
            data_dictionary['sprite_size'] = sprite_size

            all_animation_sequences = dict()
            for seq in data_dictionary['sequences']:
                state, direction = seq.split('_', maxsplit=1)
                key = AnimationState[state.upper()], AnimationDirection[direction.upper()]

                repeat = data_dictionary['sequences'][seq]['repeat']
                all_frames = data_dictionary['sequences'][seq]['frames']

                hashes = []
                for *frame, duration in all_frames:
                    img_hash = f"{str(frame[0])}_{str(frame[1])}_{os.path.basename(data_dictionary['sprite_sheet'])}"
                    if img_hash not in self._images:
                        clipping_rect = pygame.Rect(
                            frame[1] * sprite_size.x, frame[0] * sprite_size.y, sprite_size.x, sprite_size.y
                        )
                        image = sprite_sheet.subsurface(clipping_rect)
                        self._images[img_hash] = image
                    hashes.extend([img_hash] * duration)

                all_animation_sequences[key] = AnimationSequence(hashes, repeat)

                # Add right animations inverted and in reverse order
                if key[1] == AnimationDirection.RIGHT:
                    inverted_key = key[0], AnimationDirection.LEFT
                    new_hashes = []
                    for img_hash in hashes:
                        new_img_hash = f'inverted_{img_hash}'
                        if new_img_hash not in self._images:
                            img = self._images[img_hash]
                            new_img = pygame.transform.flip(img, flip_x=True, flip_y=False)
                            self._images[new_img_hash] = new_img
                        new_hashes.append(new_img_hash)

                    all_animation_sequences[inverted_key] = AnimationSequence(new_hashes, repeat)

            data_dictionary['sequences'] = all_animation_sequences
            animation_data = AnimationData(**data_dictionary)

        return animation_data

    def _get_matching_paths(self, file_name: str) -> str:
        matching_paths = list(Path(self.resource_root_path).glob(f'**/{Path(file_name)}', recurse_symlinks=True))
        if matching_paths and len(matching_paths) == 1:
            return matching_paths[0]
        elif matching_paths:
            raise ValueError(f'More than one file found for the resource: {matching_paths}')
        else:
            raise ValueError(f'File "{file_name}" was not found anywhere under {self.resource_root_path}')

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

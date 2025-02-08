"""
Stores all the game immutable data, i.e., designed for initializing all kinds of settings at runtime.
"""
import json
from typing import NamedTuple

import pygame

from yazelc.utils.game_utils import IVec


class PlayerConfig(NamedTuple):
    velocity: float
    velocity_diagonal: float
    hitbox_size: IVec
    hitbox_offset: IVec
    skin_depth: int
    animation: str
    sprite_depth: int
    interactive_range: IVec
    prefer_up_down_animation: bool  # If the animation will be the one for up and down when moving diagonally
    weapon: dict  # TODO: Temporary: To be changed.


class FontConfig(NamedTuple):
    name: str
    properties: dict


class WindowConfig(NamedTuple):
    resolution: IVec
    bgcolor: pygame.Color


class TextBoxConfig(NamedTuple):
    triangle_signal_vertices: list[IVec]
    rect_signal: pygame.Rect
    rect: pygame.Rect
    margin: IVec
    extra_line_spacing: int
    depth: int
    blinking: int
    bgcolor: pygame.Color
    font: FontConfig
    scroll_sound: str


class Settings(NamedTuple):
    window: WindowConfig
    text_box: TextBoxConfig
    player: PlayerConfig

    @classmethod
    def load_from_json(cls, path: str, **overwrites: dict):
        """
        Generates the tuple form a json and optionally overwrites the values before creating the namedtuple.
        Useful for doing adhoc changes of the general configuration
        """
        with open(path) as read_file:
            data_dictionary = json.load(read_file, object_hook=cls._object_hook)

        for key in overwrites:
            data_dictionary[key].update(overwrites[key])

        window_cfg = WindowConfig(**data_dictionary["window"])
        text_box_cfg = TextBoxConfig(**data_dictionary["text_box"])
        player_cfg = PlayerConfig(**data_dictionary["player"])

        return cls(window_cfg, text_box_cfg, player_cfg)

    @staticmethod
    def _object_hook(json_object: dict):
        for key, value in json_object.items():
            if isinstance(value, list):
                transformed = Settings.transform_lists(key, value)
                json_object[key] = transformed
            elif key == "font":
                json_object[key] = FontConfig(**value)

        return json_object

    @staticmethod
    def transform_lists(key: str, element: list | int | float | str):
        """
        Transforms recursively the lists in the json. If a list have two integer elements then it will return an immutable
        vector, i.e., IVec, if it has more than 3 then it will transform to a pygame.Color
        """
        if isinstance(element, list):
            if len(element) == 2 and all(map(lambda x: isinstance(x, int), element)):
                value = IVec(*element)
            elif len(element) >= 3 and all(map(lambda x: isinstance(x, int), element)) and 'color' in key.lower():
                value = pygame.Color(*element[:4])
            elif len(element) == 4 and all(map(lambda x: isinstance(x, int), element)):
                value = pygame.Rect(*element)
            else:
                value = tuple(Settings.transform_lists(key, sub_ele) for sub_ele in element)
        else:
            value = element
        return value

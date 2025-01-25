from __future__ import annotations

from enum import Enum
from typing import NamedTuple

from yazelc.utils.game_utils import IVec


class AnimationState(Enum):
    WALKING = 0
    ATTACKING = 1
    NONE = 2

    @classmethod
    def __missing__(cls, key):
        return cls.NONE


class AnimationDirection(Enum):
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3
    NONE = 4

    @classmethod
    def __missing__(cls, key):
        return cls.NONE


class AnimationSequence(NamedTuple):
    """ Represents the surfaces id in the sequence they must be played on each tick"""
    sequence: list[str]
    repeat: bool

    def get_image_id(self, frame: int) -> str:
        """ Returns the image id associated to the input frame"""
        return self.sequence[frame]


class AnimationData(NamedTuple):
    sprite_sheet: str
    sprite_size: IVec
    sequences: dict[tuple[AnimationState, AnimationDirection], AnimationSequence]

    def get_sequence(self, state: AnimationState, direction: AnimationDirection) -> AnimationSequence:
        return self.sequences[(state, direction)]

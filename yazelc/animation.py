from __future__ import annotations

from enum import Enum
from typing import NamedTuple

from yazelc.utils.game_utils import IVec


# TODO: Move these two enums to somewhere else non-animation related and more general
class EntityState(Enum):
    MOVING = 0
    ATTACKING = 1
    NONE = 2

    @classmethod
    def __missing__(cls, key):
        return cls.NONE


class EntityDirection(Enum):
    DOWN = 0
    LEFT = 1
    UP = 2
    RIGHT = 3
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
    sequences: dict[tuple[EntityState, EntityDirection], AnimationSequence]

    def get_sequence(self, state: EntityState, direction: EntityDirection) -> AnimationSequence:
        return self.sequences[(state, direction)]

from dataclasses import dataclass as component
from dataclasses import field, InitVar
from typing import Dict, Callable, List

import pygame

from unnamed_adventure_game.animation import AnimationStrip, flip_strip_sprites
from unnamed_adventure_game.utils.game import Direction, Status


@component
class Position:
    x: int = 0
    y: int = 0


@component
class Velocity:
    x: float = 0.0
    y: float = 0.0


@component
class State:
    """ State of being (usually a "moving" entity) used in different systems """
    direction: Direction = Direction.SOUTH
    status: Status = Status.IDLE

    previous_direction: Direction = field(init=False)
    previous_status: Status = field(init=False)

    def __post_init__(self):
        self.previous_direction = self.direction
        self.previous_status = self.status


@component
class Renderable:
    image: pygame.Surface
    depth: int = 100
    width: int = field(init=False)
    height: int = field(init=False)

    def __post_init__(self):
        self.width = self.image.get_width()
        self.height = self.image.get_height()


@component
class WallTag:
    """ Tag to keep track of collidable walls"""
    pass


@component
class Health:
    points: int = 10
    cool_down_frames: int = 20  # frame of invincibility
    cool_down_counter: int = field(init=False, default=0)


@component
class HitBox:
    x_pos: InitVar[int]
    y_pos: InitVar[int]
    width: InitVar[int]
    height: InitVar[int]
    scale_offset: int = 0
    rect: pygame.Rect = field(init=False)

    def __post_init__(self, x_pos: int, y_pos: int, width: int, height: int):
        self.rect = pygame.Rect(x_pos, y_pos, width, height)
        self.rect.inflate_ip(self.scale_offset, self.scale_offset)


@component
class Input:
    block_counter: int = field(init=False, default=0)


@component
class EnemyTag:
    """ Tags enemies and represent the value when colliding with them """
    pass


@component
class Weapon:
    damage: int = 5
    active_frames: int = 20  # -1 means is infinite
    freeze_frames: int = 0  # frames of input blocked when hit
    recoil_velocity: int = 0


@component
class Script:
    """ Calls a function with the parent entity ID passed as an argument """
    function: Callable[[int], None]
    delay: int


@component
class Door:
    target_scene: str
    target_x: int
    target_y: int


@component
class Animation:
    """
    Needs at least to get one animation stripe (idle_down) to instantiate this component. No need of "left" animation
    stripe as we can just "flip" the right one
    """
    index: int = field(init=False, default=0)
    frame_counter: int = field(init=False, default=0)
    strips: Dict[Status, Dict[Direction, List[pygame.Surface]]] = field(init=False)

    idle_down: InitVar[AnimationStrip]
    idle_up: InitVar[AnimationStrip] = None
    idle_left: InitVar[AnimationStrip] = None

    move_down: InitVar[AnimationStrip] = None
    move_up: InitVar[AnimationStrip] = None
    move_left: InitVar[AnimationStrip] = None

    attack_down: InitVar[AnimationStrip] = None
    attack_up: InitVar[AnimationStrip] = None
    attack_left: InitVar[AnimationStrip] = None

    def __post_init__(self,
                      idle_down: AnimationStrip, idle_up: AnimationStrip, idle_left: AnimationStrip,
                      move_down: AnimationStrip, move_up: AnimationStrip, move_left: AnimationStrip,
                      attack_down: AnimationStrip, attack_up: AnimationStrip, attack_left: AnimationStrip):
        """
        Creates a dictionary with the as values images surfaces and the states as keys
        """

        idle_right = move_right = attack_right = None
        if idle_left:
            idle_right = flip_strip_sprites(idle_left)
        if move_left:
            move_right = flip_strip_sprites(move_left)
        if attack_left:
            attack_right = flip_strip_sprites(attack_left, reverse_order=False)  # May not be general

        self.strips = {
            Status.IDLE: {Direction.NORTH: idle_up, Direction.WEST: idle_left,
                          Direction.SOUTH: idle_down, Direction.EAST: idle_right},
            Status.MOVING: {Direction.NORTH: move_up, Direction.WEST: move_left,
                            Direction.SOUTH: move_down, Direction.EAST: move_right},
            Status.ATTACKING: {Direction.NORTH: attack_up, Direction.WEST: attack_left,
                               Direction.SOUTH: attack_down, Direction.EAST: attack_right}
        }

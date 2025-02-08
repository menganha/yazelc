from dataclasses import dataclass as component
from dataclasses import field, InitVar
from enum import Enum, auto

import pygame

from yazelc.animation import AnimationSequence
from yazelc.font import Font
from yazelc.items import CollectableItemType
from yazelc.tween import TweenFunction
from yazelc.utils.game_utils import Direction, Status, IVec
from yazelc.utils.timer import Timer


class Vec(pygame.Vector2):
    pass


class Position(Vec):
    """
    Absolute Position of the entity.
    If "is_relative" is true, it means that is the position with respect to the camera
    """

    def __init__(self, x: float = 0.0, y: float = 0.0, is_relative: bool = False):
        super().__init__(x, y)
        self.prev_x: float = float(x)
        self.prev_y: float = float(y)
        self.is_relative = is_relative

    def __setattr__(self, key, value):
        if key in ('x', 'y'):
            old_value = getattr(self, key)
            setattr(self, f'prev_{key}', old_value)
        super().__setattr__(key, value)


class Velocity(Vec):
    ZERO_THRESHOLD = 1e-3


class Acceleration(Velocity): pass


@component
class Move:
    velocity: float
    goal: IVec
    time_steps: int = -1
    vel_x: float = 0.0
    vel_y: float = 0.0


@component
class Sign:
    """ Used for dialogs or signs in game """
    text: str


@component
class InteractorTag:
    """ Tag entity with Hitbox to signal the player interacting with colliding object """
    pass


@component
class TweenPosition:
    function: TweenFunction
    direction: Direction
    length: float
    n_frames: int
    rest_frames: int = 0  # Frames to rest at the end of the tween
    frame_counter: int = field(init=False, default=1)
    previous_relative_position: float = field(init=False, default=0.0)


@component
class Renderable:
    image: pygame.Surface
    depth: int = 100  # Depth is just over the background, i.e., background = 0, foreground, 1000, foreforeground = 2000
    width: int = field(init=False)
    height: int = field(init=False)

    def __post_init__(self):
        self.width = self.image.get_width()
        self.height = self.image.get_height()


class MenuType(Enum):
    DEATH = auto()
    PAUSE = auto()
    START = auto()


@component
class Menu:
    menu_type: MenuType
    title: str
    items: list[str]
    font: Font
    item_idx_x: int = 0
    item_idx_y: int = 0

    def __len__(self):
        return len(self.items)


@component
class Particle:
    color: pygame.Color


@component
class BlendEffect:
    time: InitVar[int]
    blink_interval: int = 5
    timer: Timer = field(init=False)  # frames of invincibility

    def __post_init__(self, time: int):
        self.timer = Timer(time)


@component
class Health:
    points: int = 10
    max_points: int = 10
    cooldown_time: InitVar[int] = 20
    cooldown_timer: Timer = field(init=False)  # frames of invincibility

    def __post_init__(self, cooldown_time: int):
        self.cooldown_timer = Timer(cooldown_time)


class HitBox(pygame.Rect):
    """
    Pygame is made such that hitboxes contain also a position. Therefore, is difficult to separate the components, i.e.,
    Position and a "Hitbox" component in a "clean way". We have opted for the approach where the Hitbox has a position
    embedded in the component but does not count as a real Position component. Nevertheless, this internal position of the
    Hitbox also represent the absolute position of it.

    In addition to the regular bounding hitbox we can optionally specify a "skin depth" which will define two additional
    hitboxes. These are used to implement the "soft corner collision" seen in games like Zelda: A Link to the Past.
    """

    def __init__(self, x_pos: int, y_pos: int, width: int, height: int, solid: bool = False, x_off: int = 0, y_off: int = 0,
                 skin_depth: int = 0):
        super().__init__(x_pos, y_pos, width, height)
        self.solid = solid
        self.offset = IVec(x_off, y_off)
        self.skin_depth = skin_depth


@component
class Brain:
    """ Brain given to an NPC character / Enemy AI"""
    think_frames: InitVar[int]
    behaviour_type: int = 0
    timer: Timer = field(init=False)
    block_timer: Timer = field(init=False)

    def __post_init__(self, think_frames: int):
        self.timer = Timer(think_frames)
        self.block_timer = Timer()


@component
class Collectable:
    """ Collectable items tag """
    item_type: CollectableItemType
    value: int = 1
    in_chest: bool = False


@component
class Enemy:
    """ Tags enemies and represent the value when colliding with them """
    type: str  # Also labels the corresponding animation


@component
class Weapon:
    damage: int = 5
    active_frames: InitVar[int] = 20  # -1 means is infinite
    freeze_frames: int = 0  # frames of input blocked when hit
    recoil_velocity: int = 0
    active_timer: Timer = field(init=False)

    def __post_init__(self, active_frames: int):
        self.active_timer = Timer(active_frames)


@component
class Door:
    target_map: str
    target_x: int
    target_y: int


@component()
class State:
    """ Helper component for general state of objects """
    status: Status
    direction: Direction

    prev_status: Status = field(init=False)
    prev_direction: Direction = field(init=False)

    def __post_init__(self):
        self.prev_status = self.status
        self.prev_direction = self.direction

    def update(self):
        self.prev_status = self.status
        self.prev_direction = self.direction

    def has_changed(self) -> bool:
        return self.prev_direction != self.direction or self.prev_status != self.status


@component
class Animation:
    sequence: AnimationSequence
    frame_counter: int = 0
    is_playing: bool = False


@component
class TextBox:
    """ Text boxes used for showing the dialog """
    text: str = ''
    cursor: int = 0  # Index of the char at which the rendered text is actually in
    line_start: int = 0  # Index of the text char at which the current line starts
    x_pos: int = 0
    y_pos: int = 0
    idle: bool = False
    typing_time = 1
    counter = 0

    def next_char(self) -> str:
        return self.text[self.cursor]

    def is_at_end(self) -> bool:
        return self.cursor >= len(self.text)

    def current_sentence(self) -> str:
        """ Gives the sentence until the word (including it) at which the index is """
        sentence = self.text[self.line_start:self.cursor + 1]
        n_words = len(sentence.rstrip().split(' '))
        words = self.text[self.line_start:].split(' ')[:n_words]
        return ' '.join(words)

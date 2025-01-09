from dataclasses import dataclass as component
from dataclasses import field, InitVar
from enum import Enum, auto

import pygame

from yazelc.font import Font
from yazelc.items import CollectableItemType
from yazelc.tween import TweenFunction
from yazelc.utils.game_utils import Direction, Status, IVec
from yazelc.utils.timer import Timer


class Position(pygame.Vector2):
    """
    Absolute position of the entity, i.e., not the one relative to the window unless the absolute
    flag is on. This one is used for entities that should be on the screen no matter where the
    camera is positioned
    """

    def __init__(self, x: float = 0, y: float = 0, absolute: bool = False):
        super().__init__(x, y)
        self.absolute = absolute
        self.prev_x: float = x
        self.prev_y: float = y

    def move_ip(self, delta_x: float | int, delta_y: float | int):
        self.prev_x = self.x
        self.prev_y = self.y
        self.x += delta_x
        self.y += delta_y

    def update(self, x: float | pygame.Vector2 | tuple[float, float] | list[float] = 0, y: float = 0, ) -> None:
        self.prev_x = self.x
        self.prev_y = self.y
        super().update(x, y)

    @classmethod
    def on_screen_center(cls, surface: pygame.Surface, width: int, height: int, absolute: bool = False):
        """ Returns the Position to which the surface is centered on the screen"""
        return cls((width - surface.get_width()) // 2, (height - surface.get_height()) // 2, absolute)

    @classmethod
    def from_direction(cls, direction: Direction, length: float, absolute: bool = False):
        ivec = direction.to_ivec(length)
        return cls.from_ivec(ivec, absolute)

    @classmethod
    def from_ivec(cls, ivec: IVec, absolute: bool = False):
        return cls(ivec.x, ivec.y, absolute)


class Velocity(Position):
    ZERO_THRESHOLD = 1e-3


class Acceleration(Velocity): pass


@component
class Sign:
    """ Used for dialogs or signs in game """
    text: str
    # font: Font


@component()
class TextBox:
    """
    Text boxes used for dialog
    """
    text: str
    index: int = 0  # Index of the char at which the rendered text is actually in
    index_start: int = 0
    x_pos: int = 0
    y_pos: int = 0
    idle: bool = False  # If the text has not been displayed fully yet is waiting to be printed
    frame_tick: int = 0  # Tick integer that count the amount of frames between printing a char
    frame_delay: int = 1  # How many frames to wait until the next letter printing

    def next_char(self) -> str:
        return self.text[self.index]

    def is_at_end(self) -> bool:
        return self.index >= len(self.text)

    def current_sentence(self) -> str:
        """ Gives the sentence until the word (including it) at which the index is """
        sentence = self.text[self.index_start:self.index + 1]
        n_words = len(sentence.rstrip().split(' '))
        words = self.text[self.index_start:].split(' ')[:n_words]
        return ' '.join(words)


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

    def __init__(self, x_pos: int, y_pos: int, width: int, height: int, impenetrable: bool = False, skin_depth: int = 0,
                 destroy_on_contact: bool = False):
        super().__init__(x_pos, y_pos, width, height)
        self.impenetrable = impenetrable
        self.skin_depth = skin_depth
        self.destroy_on_contact = destroy_on_contact
        self.corner_rects: list[pygame.Rect] = []
        if self.skin_depth:
            self.corner_rects = [pygame.Rect(0, 0, skin_depth, skin_depth) for _ in range(4)]
            self._align_corner_rects_with_parent_rect()

    def move(self, x: int, y: int) -> 'HitBox':
        """ NOTE: This is not creating a "moved" copy of the original HitBox object """
        new_hitbox = super().move(x, y)
        new_hitbox.impenetrable = self.impenetrable
        new_hitbox.skin_depth = 0  # Do not copy skin information as this will make the
        new_hitbox.corner_rects = None
        return new_hitbox  # noqa  C implementation of pygame.Rect is aware that we are subclassing

    def move_ip(self, x: int, y: int):
        """ Move also the internal boxes """
        super().move_ip(x, y)
        for corner_r in self.corner_rects:
            corner_r.move_ip(x, y)

    def collides_with_corner_points(self, rect: pygame.Rect) -> int:
        point_list = [
            [sum(ele) for ele in zip(self.corner_rects[0].topright, (-1, -1))],
            [sum(ele) for ele in zip(self.corner_rects[0].bottomleft, (-1, -1))],
            [sum(ele) for ele in zip(self.corner_rects[1].topleft, (-1, 0))],
            [sum(ele) for ele in zip(self.corner_rects[1].bottomright, (-1, 0))],
            self.corner_rects[2].topright,
            self.corner_rects[2].bottomleft,
            [sum(ele) for ele in zip(self.corner_rects[3].topleft, (0, -1))],
            self.corner_rects[3].bottomright,
        ]
        for point in point_list:
            if rect.collidepoint(*point):
                return True
        else:
            return False

    def __setattr__(self, key, value):
        if hasattr(self, 'corner_rects') and self.corner_rects:
            super().__setattr__(key, value)
            self._align_corner_rects_with_parent_rect()
        else:
            super().__setattr__(key, value)

    def _align_corner_rects_with_parent_rect(self):
        self.corner_rects[0].topleft = self.topleft  # Define them in counterclockwise direction starting from topleft
        self.corner_rects[1].bottomleft = self.bottomleft
        self.corner_rects[2].bottomright = self.bottomright
        self.corner_rects[3].topright = self.topright


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
    strip: list[pygame.Surface]
    frame_sequence: list[int]
    one_loop: bool = False
    index: int = field(init=False)
    frame_counter: int = field(init=False)
    is_playing: bool = field(init=False, default=True)

    def __post_init__(self):
        self.frame_counter = 0
        self.index = 0

    @classmethod
    def from_delay(cls, strip: list[pygame.Surface], delay: int, one_loop: bool = False):
        frame_sequence = [idx for idx in range(len(strip)) for _ in range(delay)]
        return cls(strip, frame_sequence, one_loop)

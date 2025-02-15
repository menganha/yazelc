import abc
from enum import Enum, auto

from yazelc.event.events import eventclass


class Button(Enum):
    """ Buttons on the controller. These are the only inputs the game will recognize """
    A = auto()
    B = auto()
    X = auto()
    Y = auto()
    L = auto()
    R = auto()
    START = auto()
    SELECT = auto()
    UP = auto()
    LEFT = auto()
    DOWN = auto()
    RIGHT = auto()

    DEBUG = auto()


class Controller(abc.ABC):
    """ Main interface to game input """

    @abc.abstractmethod
    def update(self):
        """ Updates the state of the buttons """
        pass

    @abc.abstractmethod
    def is_button_down(self, button: Button) -> bool:
        pass

    @abc.abstractmethod
    def is_button_pressed(self, button: Button) -> bool:
        pass

    @abc.abstractmethod
    def is_button_released(self, button: Button) -> bool:
        pass


@eventclass
class ButtonDownEvent:
    """ If the button is just pressed"""
    button: Button


@eventclass
class ButtonPressedEvent:
    """ If the button has just been pressed, i.e., not pressed on the previous polling check """
    button: Button


@eventclass
class ButtonReleasedEvent:
    button: Button

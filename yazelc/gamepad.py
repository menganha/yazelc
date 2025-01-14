from copy import copy
from enum import Enum

import pygame

from yazelc.controller import Controller, Button


class Gamepad(Controller):
    """ Represents a joystick controller """

    class GamepadButton(Enum):
        """ Buttons on the Gamepad"""
        A = 0
        B = 1
        X = 2
        Y = 3
        L = 4
        R = 5
        SELECT = 6
        START = 7
        UP = 19
        DOWN = 21
        LEFT = 9
        RIGHT = 11

    BUTTON_MAP = {
        Button.A: GamepadButton.A,
        Button.B: GamepadButton.B,
        Button.X: GamepadButton.X,
        Button.Y: GamepadButton.Y,
        Button.L: GamepadButton.L,
        Button.R: GamepadButton.R,
        Button.SELECT: GamepadButton.SELECT,
        Button.START: GamepadButton.START,
        Button.UP: GamepadButton.UP,
        Button.DOWN: GamepadButton.DOWN,
        Button.LEFT: GamepadButton.LEFT,
        Button.RIGHT: GamepadButton.RIGHT
    }

    def __init__(self, gamepad: pygame.joystick.Joystick):
        self.currentKeyStates = {}
        self.previousKeyStates = {}
        self.gamepad = gamepad

    def update(self):
        self.previousKeyStates = copy(self.currentKeyStates)
        for button in self.GamepadButton:
            if button in (self.GamepadButton.LEFT, self.GamepadButton.RIGHT):
                self.currentKeyStates[button] = round(self.gamepad.get_axis(0)) + 10 == button.value
            elif button in (self.GamepadButton.UP, self.GamepadButton.DOWN):
                self.currentKeyStates[button] = round(self.gamepad.get_axis(1)) + 20 == button.value
            else:
                self.currentKeyStates[button] = self.gamepad.get_button(button.value)

    def is_button_down(self, button: Button) -> bool:
        if not self.currentKeyStates or not self.previousKeyStates:
            return False
        key_code = self.BUTTON_MAP[button]
        return self.currentKeyStates[key_code]

    def is_button_pressed(self, button: Button) -> bool:
        if not self.currentKeyStates or not self.previousKeyStates:
            return False
        key_code = self.BUTTON_MAP[button]
        return self.currentKeyStates[key_code] and not self.previousKeyStates[key_code]

    def is_button_released(self, button: Button) -> bool:
        if not self.currentKeyStates or not self.previousKeyStates:
            return False
        key_code = self.BUTTON_MAP[button]
        return not self.currentKeyStates[key_code] and self.previousKeyStates[key_code]

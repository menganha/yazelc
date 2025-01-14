import pygame

from yazelc.controller import Controller, Button


class Keyboard(Controller):
    """ Represents a keyboard controller """

    BUTTON_MAP = {
        Button.A: pygame.K_x,
        Button.B: pygame.K_z,
        Button.X: pygame.K_s,
        Button.Y: pygame.K_a,
        Button.L: pygame.K_d,
        Button.R: pygame.K_c,
        Button.START: pygame.K_RETURN,
        Button.SELECT: pygame.K_v,
        Button.UP: pygame.K_UP,
        Button.DOWN: pygame.K_DOWN,
        Button.LEFT: pygame.K_LEFT,
        Button.RIGHT: pygame.K_RIGHT
    }

    def __init__(self):
        self.currentKeyStates = None
        self.previousKeyStates = None

    def update(self):
        self.previousKeyStates = self.currentKeyStates
        self.currentKeyStates = pygame.key.get_pressed()

    def is_button_down(self, button: Button) -> bool:
        if self.currentKeyStates is None or self.previousKeyStates is None:
            return False
        key_code = self.BUTTON_MAP[button]
        return self.currentKeyStates[key_code]

    def is_button_pressed(self, button: Button) -> bool:
        if self.currentKeyStates is None or self.previousKeyStates is None:
            return False
        key_code = self.BUTTON_MAP[button]
        return self.currentKeyStates[key_code] and not self.previousKeyStates[key_code]

    def is_button_released(self, button: Button) -> bool:
        if self.currentKeyStates is None or self.previousKeyStates is None:
            return False
        key_code = self.BUTTON_MAP[button]
        return not self.currentKeyStates[key_code] and self.previousKeyStates[key_code]

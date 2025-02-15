import logging.config
import os

import pygame

from yazelc.resource_manager import ResourceManager
from yazelc.scenes import base_scene
from yazelc.systems.player_system import PlayerState

pygame.init()

from yazelc.gamepad import Gamepad
from yazelc.keyboard import Keyboard
from collections import deque

from yazelc.settings import Settings
from yazelc.scenes import new_gameplay_scene
from yazelc.logging_config import INFO_CONFIG, ERROR_CONFIG, DEBUG_CONFIG
from yazelc import save

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    log_config_level = os.getenv('YAZELC_LOG')
    if log_config_level == 'INFO':
        logging.config.dictConfig(INFO_CONFIG)
    elif log_config_level == 'DEBUG':
        logging.config.dictConfig(DEBUG_CONFIG)
    else:
        logging.config.dictConfig(ERROR_CONFIG)

    settings = Settings.load_from_json('data/settings.json')

    window = pygame.display.set_mode(settings.window.resolution, pygame.SCALED, vsync=1)

    pygame.joystick.init()
    if pygame.joystick.get_count():
        controller = Gamepad(pygame.joystick.Joystick(0))
        logger.info('Using gamepad controller')
    else:
        controller = Keyboard()
        pygame.joystick.quit()
        logger.info('Using keyboard controller')

    save_file = os.path.join('link.save')  # NOTE: Temporary solution until we create a loader and saver ui from the main game
    save = save.load_state(save_file) if os.path.exists(save_file) else PlayerState()
    resources = ResourceManager()
    scene = base_scene.Scene(window, controller, resources, settings, save)
    new_gameplay_scene.init(scene)
    scenes_queue = deque([scene])  # TODO: We could implement this as a single-sided linked list, it is just a stack after all

    needs_init = True
    while scenes_queue:

        current_scene = scenes_queue[-1]
        current_scene.finished = False
        current_scene.next_scene = None

        while not current_scene.finished:
            base_scene.update(current_scene)

        if current_scene.next_scene:
            scenes_queue.append(current_scene.next_scene)
        elif current_scene.jump_to_exit:
            scenes_queue.clear()
        else:  # If it's on the queue it was already initialized
            scenes_queue.pop()

    pygame.quit()

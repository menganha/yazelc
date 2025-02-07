import logging.config
import os

import pygame

pygame.init()

from yazelc.gamepad import Gamepad
from yazelc.keyboard import Keyboard
from collections import deque

from yazelc.settings import Settings
from yazelc.scenes.new_gameplay_scene import GameplayScene
from yazelc.logging_config import INFO_CONFIG, ERROR_CONFIG, DEBUG_CONFIG

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

    # NOTE: Temporary solution until we create a loader and saver ui from the main game
    save_file = os.path.join('link.save')
    scenes_queue = deque([GameplayScene(window, controller, settings, save_file)])

    while scenes_queue:
        current_scene = scenes_queue.pop()

        logger.info(f'Entering scene {current_scene.__class__}')
        current_scene.on_enter()

        while not current_scene.finished:
            current_scene.update()

        logger.info(f'Exiting scene {current_scene.__class__}')
        current_scene.on_exit()

        if current_scene.next_scene:
            scenes_queue.append(current_scene)

    pygame.quit()

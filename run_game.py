import logging
import os

import pygame

pygame.init()

from yazelc.gamepad import Gamepad
from yazelc.keyboard import Keyboard
from collections import deque

from settings import Settings
from yazelc.scenes.gameplay_scene import GameplayScene
from yazelc.resource_manager import ResourceManager

SETTINGS_FILENAME = 'settings.json'

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s.%(msecs)03d [%(levelname)s]: %(message)s',
                        datefmt='%I:%M:%S'
                        )

    root_folder = os.path.dirname(os.path.abspath(__file__))
    resource_manager = ResourceManager(root_folder)

    configuration_file_path = resource_manager.get_matching_path(SETTINGS_FILENAME)
    settings = Settings.load_from_json(configuration_file_path)

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
    save_state = os.path.join(resource_manager.get_user_path('yazelc'), 'yazelc1.save')
    scenes_queue = deque([GameplayScene(window, controller, resource_manager, settings, game_data)])

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

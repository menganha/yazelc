import logging
import sys
from pathlib import Path

import pygame

pygame.init()

from yazelc.gamepad import Gamepad
from yazelc.keyboard import Keyboard


from yazelc import config as cfg
from yazelc.scenes import scene_manager
from yazelc.scenes.gameplay_scene import GameplayScene
from yazelc.scenes.intro_scene import IntroScene
from yazelc.utils.game_utils import IVec

INITIAL_MAP = Path('data', 'overworld', 'overworld_1.tmx')
INITIAL_MUSIC_PATH = Path('assets', 'music', 'Quantic_y_Los_Míticos_del_Ritmo-Hotline_Bling.ogg')
INITIAL_POS = IVec(10, 24)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s.%(msecs)03d [%(levelname)s]: %(message)s',
                        datefmt='%I:%M:%S')

    window = pygame.display.set_mode((cfg.RESOLUTION.x, cfg.RESOLUTION.y), pygame.SCALED, vsync=1)

    pygame.joystick.init()
    if pygame.joystick.get_count():
        controller = Gamepad(pygame.joystick.Joystick(0))
        logging.info('Using gamepad controller')
    else:
        controller = Keyboard()
        pygame.joystick.quit()
        logging.info('Using keyboard controller')

    if len(sys.argv) > 1 and sys.argv[1].lower() == 'gameplay':
        map_path = Path(sys.argv[2]) if sys.argv[2:] else INITIAL_MAP
        initial_pos = IVec(int(sys.argv[3]) if sys.argv[3:] else INITIAL_POS.x, int(sys.argv[4]) if sys.argv[4:] else INITIAL_POS.y)
        scene = GameplayScene(window, controller, map_path, initial_pos, music_path=INITIAL_MUSIC_PATH)
    else:
        scene = IntroScene(window, controller)

    # Get the main input device
    scene_manager.run_game_loop(initial_scene=scene)
    pygame.quit()

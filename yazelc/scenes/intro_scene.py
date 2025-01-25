from pathlib import Path

import pygame

from yazelc import config as cfg
from yazelc.components import Renderable, Position, MenuType
from yazelc.cutscene.fade_task import FadeInTask, FadeOutTask
from yazelc.cutscene.move_task import MoveTask
from yazelc.cutscene.spawn_task import SpawnTask
from yazelc.cutscene.wait_task import WaitTask
from yazelc.event.events import ChangeSceneEvent
from yazelc.menu import menu_box
from yazelc.scenes.base_scene import BaseScene
from yazelc.scenes.gameplay_scene import GameplayScene
from yazelc.systems.cutscene_system import CutsceneSystem
from yazelc.systems.dialog_menu_system import DialogMenuSystem
from yazelc.systems.movement_system import MovementSystem
from yazelc.systems.render_system import RenderSystem
from yazelc.tween import TweenFunction
from yazelc.utils.game_utils import IVec

ASSET_PATH = Path('assets', 'sprites')
PG_LOGO = ASSET_PATH / 'pygame_powered_logo.png'
SHIELD_LOGO = ASSET_PATH / 'shield_logo.png'
MUSIC_PATH = Path('assets', 'music', 'Quantic_Flowering_Inferno-Cumbia_Sobre_el_Mar.ogg')

FONT_PATH = Path('assets', 'font', 'Anonymous Pro.ttf')
FONT_COLOR = cfg.C_WHITE
FONT_SIZE = 11
TITLE_TEXT = 'A game by\nClimacus'

INITIAL_MAP = Path('data', 'overworld', 'overworld_1.tmx')
INITIAL_MUSIC_PATH = Path('assets', 'music', 'Quantic_y_Los_Míticos_del_Ritmo-Hotline_Bling.ogg')
INITIAL_POS = IVec(10, 24)


class IntroScene(BaseScene):

    def on_enter(self):
        # load resources
        pg_logo_surface = self.world.resource_manager.load_image(PG_LOGO)
        pg_logo_surface.set_alpha(0)
        scale = 0.10
        pg_logo_surface = pygame.transform.smoothscale(pg_logo_surface,
                                                       (int(pg_logo_surface.get_width() * scale),
                                                        int(pg_logo_surface.get_height() * scale)))
        shield_surface = self.world.resource_manager.load_image(SHIELD_LOGO)
        pygame.mixer.music.load(MUSIC_PATH)
        pygame.mixer.music.play(-1)

        font = self.world.resource_manager.add_font(FONT_PATH, FONT_SIZE, FONT_COLOR, 'font')

        # Alternative source
        credit_surface = font.render(TITLE_TEXT, center=True)

        # Entities
        pg_logo_ent = self.world.create_entity(Position.on_screen_center(pg_logo_surface), Renderable(pg_logo_surface))

        credit_ent_components = (Position.on_screen_center(credit_surface), Renderable(credit_surface))

        shield_ent = self.world.create_entity(Position(0, -150, absolute=True), Renderable(shield_surface))

        shield_ent_2 = self.world.create_entity(Position(0, -150, absolute=True), Renderable(shield_surface))

        title = ''
        items = ['Start Game', 'Credits', 'Exit']
        menu_type = MenuType.START  # TODO: Callback is stored somewhere else. This seems highly un-encapsulated
        menu_components = menu_box.get_components(title, items, font, menu_type)

        # Set cutscene
        task_list_main = [
            FadeInTask(pg_logo_ent, tween_function=TweenFunction.EASE_OUT_CUBIC, duration_frames=300),
            WaitTask(duration_frames=100),
            FadeOutTask(pg_logo_ent, tween_function=TweenFunction.EASE_OUT_CUBIC, duration_frames=150),
            WaitTask(duration_frames=100),
            SpawnTask(*credit_ent_components, duration_frames=350),
            WaitTask(duration_frames=250),
            MoveTask(shield_ent, final_pos=IVec(0, 90), duration_frames=350),
            WaitTask(duration_frames=50),
            SpawnTask(*menu_components, duration_frames=-1)
        ]

        secondary_task_list = [
            MoveTask(shield_ent_2, final_pos=IVec(200, 90), duration_frames=350),
        ]

        # Set systems
        render_sys = RenderSystem(self.window)
        cutscene_sys = CutsceneSystem(task_list_main, secondary_task_list)
        dialog_sys = DialogMenuSystem()
        self.world.add_processor(render_sys)
        self.world.add_processor(cutscene_sys)
        self.world.add_processor(dialog_sys)
        self.world.add_processor(MovementSystem())

        self.event_manager.subscribe_handler(dialog_sys)

    def on_change_scene(self, change_scene_event: ChangeSceneEvent):
        if change_scene_event.next_scene == 'gameplay':
            self.finished = True
            self.next_scene = GameplayScene(self.window, self.controller, INITIAL_MAP, INITIAL_POS, music_path=INITIAL_MUSIC_PATH)

    def on_exit(self):
        pass

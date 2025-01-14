import pygame

pygame.init()

import zesper
from event.event_manager import EventManager, ButtonDownEvent, CloseWindowEvent

from yazelc.config import Config
from yazelc.font import Font
from yazelc.resource_manager import ResourceManager
from yazelc.systems.dialog_menu_system import DialogMenuSystem
from yazelc.systems.render_system import RenderSystem
from yazelc.components import Sign, Renderable, Position
from yazelc.keyboard import Keyboard, Button


class Game:
    def __init__(self):
        self.is_running = True
        self.waiting_for_close_dialog = False

        self.config = Config.load_from_json('../settings.json', window={'bgcolor': pygame.Color(255, 255, 255)})
        self.resource_manager = ResourceManager('../../assets')
        self.event_manager = EventManager()
        self.world = zesper.World()
        self.controller = Keyboard()

        self.resource_manager.add('Anonymous Pro.ttf')

        window = pygame.display.set_mode(self.config.window.resolution, pygame.SCALED, vsync=1)

        dialog_menu_system = DialogMenuSystem(self.config, self.resource_manager)
        render_system = RenderSystem(window, self.config)
        self.world.add_processor(dialog_menu_system)
        self.world.add_processor(render_system)

        # Sign entity
        sign = Sign('A sample text that is very big and will serve us to test the dialog event system. '
                    'This text should appear cover more than one box'
                    )
        self.sign_ent_id = self.world.create_entity(sign)

        # Message box
        font = Font(self.resource_manager.get('Anonymous Pro.ttf'), 11, pygame.Color(0, 0, 0))
        x_pos, y_pos = 10, 10
        for msg in ('Press left arrow to generate text', 'Press "x" key to continue the dialog box'):
            surface = font.render(msg)
            self.world.create_entity(Renderable(surface), Position(x_pos, y_pos))
            y_pos += 20

        self.event_manager.subscribe(ButtonDownEvent, self.on_button_down, dialog_menu_system.on_input)
        self.event_manager.subscribe(dialog_menu_system.EvDialogMenuExit, self.on_dialog_exit)
        self.event_manager.subscribe(dialog_menu_system.EVDialogMenuTrigger, dialog_menu_system.on_dialog_trigger)
        self.event_manager.subscribe(CloseWindowEvent, self.on_window_closed)

    def on_button_down(self, button_event: ButtonDownEvent):
        if button_event.button == Button.LEFT and not self.waiting_for_close_dialog:
            self.event_manager.trigger_event(DialogMenuSystem.EVDialogMenuTrigger(self.sign_ent_id))
            self.waiting_for_close_dialog = True

    def on_window_closed(self, close_window_event: CloseWindowEvent):
        self.is_running = False

    def on_dialog_exit(self, dialog_exit: DialogMenuSystem.EvDialogMenuExit):
        self.waiting_for_close_dialog = False

    def run(self):
        while self.is_running:
            self.event_manager.process_all_events(self.controller, self.world)
            self.world.process()
        pygame.quit()


if __name__ == '__main__':
    app = Game()
    app.run()

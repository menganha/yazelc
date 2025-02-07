import pygame

pygame.init()

from yazelc import zesper
from yazelc.event.event_manager import EventManager, ButtonDownEvent, CloseWindowEvent

from yazelc.settings import Settings
from yazelc.resource_manager import ResourceManager
from yazelc.systems.dialog_menu_system import DialogMenuSystem, DialogMenuExitEvent, DialogMenuTriggerEvent
from yazelc.systems.render_system import RenderSystem
from yazelc.components import Sign, Renderable, Position
from yazelc.keyboard import Keyboard, Button


class Game:
    def __init__(self):
        self.is_running = True
        self.waiting_for_close_dialog = False

        self.config = Settings.load_from_json('../settings.json', window={'bgcolor': pygame.Color(255, 255, 255)})
        self.resource_manager = ResourceManager('../../')
        self.event_manager = EventManager()
        self.world = zesper.World()
        self.controller = Keyboard()
        window = pygame.display.set_mode(self.config.window.resolution, pygame.SCALED, vsync=1)

        dialog_menu_system = DialogMenuSystem(self.config, self.world, self.resource_manager)
        render_system = RenderSystem(window, self.config.window.bgcolor, self.world)

        self.list_processors = [dialog_menu_system, render_system]

        # Sign entity
        sign = Sign(
            'A sample text that is very big and will serve us to test the dialog event system. We have to '
            'write a little bit more so that we get more than one line of text. This text should appear to '
            'cover more than one box'
        )
        self.sign_ent_id = self.world.create_entity(sign)

        # Message box
        font = self.resource_manager.font('assets/font/Px437_Portfolio_6x8.ttf', pygame.Color('black'), 8)

        x_pos, y_pos = 10, 10
        msg = 'Press left arrow to generate text\nPress "x" key to continue the dialog box'
        surface = font.render(msg, extra_line_spacing=2)
        self.world.create_entity(Renderable(surface), Position(x_pos, y_pos))

        self.event_manager.subscribe(ButtonDownEvent, self.on_button_down, dialog_menu_system.on_input)
        self.event_manager.subscribe(DialogMenuExitEvent, self.on_dialog_exit)
        self.event_manager.subscribe(DialogMenuTriggerEvent, dialog_menu_system.on_dialog_trigger)
        self.event_manager.subscribe(CloseWindowEvent, self.on_window_closed)

    def on_button_down(self, button_event: ButtonDownEvent):
        if button_event.button == Button.LEFT and not self.waiting_for_close_dialog:
            self.event_manager.trigger_event(DialogMenuTriggerEvent(self.sign_ent_id))
            self.waiting_for_close_dialog = True

    def on_window_closed(self, _close_window_event: CloseWindowEvent):
        self.is_running = False

    def on_dialog_exit(self, _dialog_exit: DialogMenuExitEvent):
        self.waiting_for_close_dialog = False

    def run(self):
        while self.is_running:
            self.event_manager.process_all_events(self.controller, self.list_processors)
            self.world.process()
            for processor in self.list_processors:
                processor.process()
        pygame.quit()


if __name__ == '__main__':
    app = Game()
    app.run()

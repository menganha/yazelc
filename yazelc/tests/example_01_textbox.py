import pygame

from yazelc.controller import ButtonPressedEvent

pygame.init()

from yazelc import zesper
from yazelc.event.event_manager import EventManager, CloseWindowEvent

from yazelc.settings import Settings
from yazelc.resource_manager import ResourceManager
from yazelc.systems.dialog_menu_system import DialogMenuSystem, DialogEndEvent
from yazelc.systems.render_system import RenderSystem
from yazelc.components import Renderable, Position
from yazelc.keyboard import Keyboard, Button


class Game:
    def __init__(self):
        self.is_running = True
        self.waiting_for_close_dialog = False

        self.config = Settings.load_from_json('../../data/settings.json', window={'bgcolor': pygame.Color(255, 255, 255)})
        self.resource_manager = ResourceManager('../../')
        self.event_manager = EventManager()
        self.world = zesper.World()
        self.controller = Keyboard()
        window = pygame.display.set_mode(self.config.window.resolution, pygame.SCALED, vsync=1)

        dialog_menu_system = DialogMenuSystem(self.config.text_box, self.world, self.resource_manager)
        render_system = RenderSystem(window, self.config.window.bgcolor, self.world)

        self.list_processors = [dialog_menu_system, render_system]

        # Sign entity
        self.sign_text = (
            'A sample text that is very big and will serve us to test the dialog event system. We have to '
            'write a little bit more so that we get more than one line of text. This text should appear to '
            'cover more than one box'
        )

        # Message box
        font = self.resource_manager.font('assets/font/Px437_Portfolio_6x8.ttf', pygame.Color('black'), 8)

        x_pos, y_pos = 10, 10
        msg = 'Press left arrow to generate text\nPress "x" key to continue the dialog box'
        surface = font.render(msg, extra_line_spacing=2)
        self.world.create_entity(Renderable(surface), Position(x_pos, y_pos))

        self.event_manager.subscribe(ButtonPressedEvent, self.on_button_down, dialog_menu_system.on_button_pressed)
        self.event_manager.subscribe(DialogEndEvent, self.on_dialog_exit)
        self.event_manager.subscribe(CloseWindowEvent, self.on_window_closed)

    def on_button_down(self, button_event: ButtonPressedEvent):
        if button_event.button == Button.LEFT and not self.waiting_for_close_dialog:
            for proc in self.list_processors:
                if isinstance(proc, DialogMenuSystem):
                    proc.add_text(self.sign_text)
                    self.waiting_for_close_dialog = True

    def on_window_closed(self, _close_window_event: CloseWindowEvent):
        self.is_running = False

    def on_dialog_exit(self, _dialog_exit: DialogEndEvent):
        self.waiting_for_close_dialog = False

    def run(self):
        while self.is_running:
            self.event_manager.process_system_events()
            self.event_manager.process_controller(self.controller)
            for proc in self.list_processors:
                self.event_manager.process_queue(proc.event_queue)
            self.world.process()
            for processor in self.list_processors:
                processor.process()
        pygame.quit()


if __name__ == '__main__':
    app = Game()
    app.run()

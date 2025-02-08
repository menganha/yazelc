from yazelc.controller import Button, ButtonPressedEvent
from yazelc.event.event_manager import CloseWindowEvent
from yazelc.event.events import DebugToggleEvent
from yazelc.scenes.base_scene import BaseScene
from yazelc.systems.dialog_menu_system import DialogMenuSystem, DialogEndEvent
from yazelc.systems.render_system import RenderSystem


class DialogScene(BaseScene):

    def on_init(self):
        dialog_menu_system = DialogMenuSystem(self.settings.text_box, self.scene_state.world, self.scene_state.resources)
        render_system = RenderSystem(self.window, self.settings.window.bgcolor, self.scene_state.world)
        self.scene_state.processor_list = [dialog_menu_system, render_system]

        # Connect all events with handlers
        self.scene_state.event_manager.subscribe(CloseWindowEvent, self.on_window_close)
        self.scene_state.event_manager.subscribe(ButtonPressedEvent, dialog_menu_system.on_button_pressed, self.on_button_pressed)
        self.scene_state.event_manager.subscribe(DebugToggleEvent, render_system.on_debug_toggle)
        self.scene_state.event_manager.subscribe(DialogEndEvent, self.on_dialog_end)

    def on_exit(self):
        pass

    def on_window_close(self, _close_window_event: CloseWindowEvent):
        # TODO: Before exiting we should ask if you want to save, etc.
        self.finished = True
        self.next_scene = None

    def on_dialog_end(self, _dialog_end_event: DialogEndEvent):
        self.finished = True
        self.next_scene = None

    def on_button_pressed(self, button_released_event: ButtonPressedEvent):
        if button_released_event.button == Button.DEBUG:
            self.scene_state.event_manager.trigger_event(DebugToggleEvent())

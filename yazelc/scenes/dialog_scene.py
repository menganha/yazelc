import pygame

from yazelc import components as cmp
from yazelc.controller import ButtonDownEvent, ButtonReleasedEvent, Button
from yazelc.event.event_manager import CloseWindowEvent
from yazelc.event.events import DebugToggleEvent
from yazelc.scenes.scene import BaseScene
from yazelc.systems.dialog_menu_system import DialogMenuSystem
from yazelc.systems.render_system import RenderSystem


class DialogScene(BaseScene):

    def on_init(self):
        dialog_menu_system = DialogMenuSystem(self.settings, self.scene_state.world, self.scene_state.resources)
        render_system = RenderSystem(self.window, self.settings.window.bgcolor, self.scene_state.world)
        self.scene_state.processor_list = [dialog_menu_system, render_system]

        # Connect all events with handlers
        self.scene_state.event_manager.subscribe(CloseWindowEvent, self.on_window_close)
        self.scene_state.event_manager.subscribe(ButtonDownEvent, self.on_button_down)
        self.scene_state.event_manager.subscribe(DebugToggleEvent, render_system.on_debug_toggle)

    def on_exit(self):
        pass

    def on_window_close(self, _close_window_event: CloseWindowEvent):
        self.finished = True

    def on_button_released(self, button_released_event: ButtonReleasedEvent):
        if button_released_event.button == Button.DEBUG:
            self.scene_state.event_manager.trigger_event(DebugToggleEvent())

    def on_button_down(self, button_down_event: ButtonDownEvent):
        if button_down_event.button == Button.A:
            for entity, (text_box, renderable_) in self.scene_state.world.get_components(cmp.TextBox, cmp.Renderable):
                if text_box.idle:
                    if text_box.is_at_end():
                        self.scene_state.world.delete_entity(entity)
                        self.finished = True
                    else:
                        text_box.idle = False
                        renderable_.image.fill(self.settings.text_box.bgcolor)
                        # self.scene_state.event_queue.add(SoundTriggerEvent(self.settings.text_box.scroll_sound))

    def create_simple_text(self, text: str):
        """ Generates a text box entity """
        text_box_entity_id = self.scene_state.world.create_entity()

        background = pygame.Surface((self.settings.window.resolution.x, self.settings.text_box.height))
        background.fill(self.settings.text_box.bgcolor)

        self.scene_state.world.add_component(text_box_entity_id, cmp.TextBox(text))
        self.scene_state.world.add_component(text_box_entity_id, cmp.Renderable(image=background, depth=self.settings.text_box.image_depth))
        self.scene_state.world.add_component(text_box_entity_id, cmp.Position(0, self.settings.window.resolution.x - self.settings.text_box.height))

    # self.scene_state.event_queue.add(SoundTriggerEvent(self.settings.text_box.scroll_sound))

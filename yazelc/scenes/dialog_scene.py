from yazelc.controller import Button, ButtonPressedEvent
from yazelc.event.event_manager import CloseWindowEvent
from yazelc.event.events import DebugToggleEvent
from yazelc.scenes.base_scene import Scene
from yazelc.systems.dialog_menu_system import DialogMenuSystem, DialogEndEvent
from yazelc.systems.render_system import RenderSystem


def init(scene: Scene):
    dialog_menu_system = DialogMenuSystem(scene.settings.text_box, scene.state.world, scene.resources)
    render_system = RenderSystem(scene.window, scene.settings.window.bgcolor, scene.state.world)
    scene.state.processor_list = [dialog_menu_system, render_system]

    # Connect all events with handlers
    scene.state.event_manager.subscribe(CloseWindowEvent, on_window_close, scene)
    scene.state.event_manager.subscribe(ButtonPressedEvent, dialog_menu_system.on_button_pressed)
    scene.state.event_manager.subscribe(ButtonPressedEvent, on_button_pressed, scene)
    scene.state.event_manager.subscribe(DebugToggleEvent, render_system.on_debug_toggle)
    scene.state.event_manager.subscribe(DialogEndEvent, on_dialog_end, scene)


def on_window_close(scene: Scene, _close_window_event: CloseWindowEvent):
    # TODO: Before exiting we should ask if you want to save, etc.
    scene.finished = True
    scene.next_scene = None


def on_dialog_end(scene: Scene, _dialog_end_event: DialogEndEvent):
    scene.finished = True
    scene.next_scene = None


def on_button_pressed(scene: Scene, button_released_event: ButtonPressedEvent):
    if button_released_event.button == Button.DEBUG:
        scene.state.event_manager.trigger_event(DebugToggleEvent())

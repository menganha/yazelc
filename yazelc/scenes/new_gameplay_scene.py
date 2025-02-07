import yazelc.components as cmp
from yazelc.camera import Camera
from yazelc.controller import ButtonDownEvent, ButtonReleasedEvent, Button
from yazelc.event.event_manager import CloseWindowEvent
from yazelc.event.events import DebugToggleEvent
from yazelc.map import Map
from yazelc.scenes.scene import BaseScene
from yazelc.systems.animation_system import AnimationSystem
from yazelc.systems.collision_system import CollisionSystem
from yazelc.systems.dialog_menu_system import DialogMenuSystem
from yazelc.systems.player_system import PlayerSystem
from yazelc.systems.render_system import RenderSystem


class GameplayScene(BaseScene):

    def on_enter(self):

        map_ = Map(self.save.last_visited_map, self.scene_state.resources)
        camera = Camera(self.settings.window.resolution, map_.size)

        render_system = RenderSystem(self.window, self.settings.window.bgcolor, self.scene_state.world, camera)
        animation_system = AnimationSystem(self.scene_state.world, self.scene_state.resources)
        collision_system = CollisionSystem(self.scene_state.world)
        player_system = PlayerSystem(
            self.settings.player, self.save.inventory, self.scene_state.world, self.scene_state.resources
        )
        dialog_menu_system = DialogMenuSystem(self.settings, self.scene_state.world, self.scene_state.resources)
        self.scene_state.processor_list = [player_system, collision_system, animation_system, dialog_menu_system, render_system]

        # Generate the map
        for image, depth in map_.get_map_images():
            self.scene_state.world.create_entity(cmp.Position(), cmp.Renderable(image, depth=depth))
        for hitbox in map_.get_colliders():
            self.scene_state.world.create_entity(hitbox)
        for components in map_.get_objects():
            self.scene_state.world.create_entity(*components)

        camera.track_entity(player_system.player_entity, self.scene_state.world)
        player_system.set_position(map_.start_pos.x, map_.start_pos.y)  # Sets the default start position for that map

        # Connect all events with handlers
        self.scene_state.event_manager.subscribe(CloseWindowEvent, self.on_window_close)
        self.scene_state.event_manager.subscribe(ButtonDownEvent, player_system.on_button_down)
        self.scene_state.event_manager.subscribe(ButtonReleasedEvent, player_system.on_button_released, self.on_button_released)
        self.scene_state.event_manager.subscribe(DebugToggleEvent, render_system.on_debug_toggle)

    def on_exit(self):
        pass

    def on_window_close(self, _close_window_event: CloseWindowEvent):
        self.finished = True

    def on_button_released(self, button_released_event: ButtonReleasedEvent):
        if button_released_event.button == Button.DEBUG:
            self.scene_state.event_manager.trigger_event(DebugToggleEvent())

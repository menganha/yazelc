import yazelc.components as cmp
from yazelc.camera import Camera
from yazelc.controller import ButtonDownEvent, ButtonReleasedEvent, Button, ButtonPressedEvent
from yazelc.event.event_manager import CloseWindowEvent
from yazelc.event.events import DebugToggleEvent
from yazelc.map import Map
from yazelc.scenes.dialog_scene import DialogScene
from yazelc.scenes.scene import BaseScene
from yazelc.systems.animation_system import AnimationSystem
from yazelc.systems.collision_system import CollisionSystem, SolidEnterCollisionEvent
from yazelc.systems.dialog_menu_system import DialogTriggerEvent
from yazelc.systems.player_system import PlayerSystem
from yazelc.systems.render_system import RenderSystem


class GameplayScene(BaseScene):

    def on_init(self):

        map_ = Map(self.save_state.last_visited_map, self.scene_state.resources)
        camera = Camera(self.settings.window.resolution, map_.size)

        render_system = RenderSystem(self.window, self.settings.window.bgcolor, self.scene_state.world, camera)
        animation_system = AnimationSystem(self.scene_state.world, self.scene_state.resources)
        collision_system = CollisionSystem(self.scene_state.world)
        player_system = PlayerSystem(
            self.settings.player, self.save_state.inventory, self.scene_state.world, self.scene_state.resources
        )
        self.scene_state.processor_list = [player_system, collision_system, animation_system, render_system]

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
        self.scene_state.event_manager.subscribe(ButtonReleasedEvent, player_system.on_button_released)
        self.scene_state.event_manager.subscribe(ButtonPressedEvent, player_system.on_button_pressed, self.on_button_pressed)
        self.scene_state.event_manager.subscribe(DebugToggleEvent, render_system.on_debug_toggle)
        self.scene_state.event_manager.subscribe(SolidEnterCollisionEvent, player_system.on_solid_collision)
        self.scene_state.event_manager.subscribe(DialogTriggerEvent, self.on_dialog_menu_trigger)

    def on_exit(self):
        pass

    def on_window_close(self, _close_window_event: CloseWindowEvent):
        self.next_scene = None
        self.finished = True

    def on_button_pressed(self, button_event: ButtonPressedEvent):
        if button_event.button == Button.DEBUG:
            self.scene_state.event_manager.trigger_event(DebugToggleEvent())

    def on_dialog_menu_trigger(self, dialog_menu_trigger_event: DialogTriggerEvent):
        self.next_scene = DialogScene(self.window, self.controller, self.settings, self.save_state)
        text = self.scene_state.world.component_for_entity(dialog_menu_trigger_event.sign_ent_id, cmp.Sign).text
        renderable = cmp.Renderable(self.window.copy())
        position = cmp.Position()
        self.next_scene.scene_state.world.create_entity(position, renderable)
        self.next_scene.create_simple_text(text)
        self.finished = True

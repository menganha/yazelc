import yazelc.components as cmp
from yazelc.camera import Camera
from yazelc.controller import ButtonDownEvent, ButtonReleasedEvent, Button, ButtonPressedEvent
from yazelc.event.event_manager import CloseWindowEvent
from yazelc.event.events import DebugToggleEvent
from yazelc.map import Map
from yazelc.scenes import dialog_scene
from yazelc.scenes.base_scene import Scene, get_processor_instance
from yazelc.systems.animation_system import AnimationSystem
from yazelc.systems.collision_system import CollisionSystem, SolidEnterCollisionEvent, EnterCollisionEvent
from yazelc.systems.dialog_menu_system import DialogMenuSystem
from yazelc.systems.player_system import PlayerSystem, DialogTriggerEvent, EnterDoorEvent
from yazelc.systems.render_system import RenderSystem


def init(scene: Scene):
    map_ = Map(scene.save_state.last_visited_map, scene.resources)
    camera = Camera(scene.settings.window.resolution, map_.size)

    render_system = RenderSystem(scene.window, scene.settings.window.bgcolor, scene.scene_state.world, camera)
    animation_system = AnimationSystem(scene.scene_state.world, scene.resources)
    collision_system = CollisionSystem(scene.scene_state.world)
    player_system = PlayerSystem(
        scene.settings.player, scene.save_state.inventory, scene.scene_state.world, scene.resources
    )
    scene.scene_state.processor_list = [player_system, collision_system, animation_system, render_system]

    # Generate the map
    for image, depth in map_.get_map_images():
        scene.scene_state.world.create_entity(cmp.Position(), cmp.Renderable(image, depth=depth))
    for hitbox in map_.get_colliders():
        scene.scene_state.world.create_entity(hitbox)
    for components in map_.get_objects():
        scene.scene_state.world.create_entity(*components)

    camera.track_entity(player_system.player_entity, scene.scene_state.world)
    player_system.set_position(map_.start_pos.x, map_.start_pos.y)  # Sets the default start position for that map

    # Connect all events with handlers
    scene.scene_state.event_manager.subscribe(CloseWindowEvent, on_window_close, scene)
    scene.scene_state.event_manager.subscribe(ButtonDownEvent, player_system.on_button_down)
    scene.scene_state.event_manager.subscribe(ButtonReleasedEvent, player_system.on_button_released)
    scene.scene_state.event_manager.subscribe(ButtonPressedEvent, player_system.on_button_pressed)
    scene.scene_state.event_manager.subscribe(ButtonPressedEvent, on_button_pressed, scene)
    scene.scene_state.event_manager.subscribe(DebugToggleEvent, render_system.on_debug_toggle)
    scene.scene_state.event_manager.subscribe(SolidEnterCollisionEvent, player_system.on_solid_collision)
    scene.scene_state.event_manager.subscribe(EnterCollisionEvent, player_system.on_collision)
    scene.scene_state.event_manager.subscribe(DialogTriggerEvent, on_dialog_menu_trigger, scene)
    scene.scene_state.event_manager.subscribe(EnterDoorEvent, on_enter_door_event, scene)


def on_window_close(scene: Scene, _close_window_event: CloseWindowEvent):
    scene.next_scene = None
    scene.finished = True


def on_button_pressed(scene, button_event: ButtonPressedEvent):
    if button_event.button == Button.DEBUG:
        scene.scene_state.event_manager.trigger_event(DebugToggleEvent())


def on_enter_door_event(scene, enter_door_event: EnterDoorEvent):
    scene.save_state.last_visited_map = enter_door_event.map
    next_scene = type(scene)(scene.window, scene.controller, scene.resources, scene.settings, scene.save_state)
    scene.next_scene = next_scene
    scene.finished = True


def on_dialog_menu_trigger(scene, dialog_menu_trigger_event: DialogTriggerEvent):
    new_dialog_scene = Scene(scene.window, scene.controller, scene.resources, scene.settings, scene.save_state)
    dialog_scene.init(new_dialog_scene)

    scene.next_scene = new_dialog_scene
    scene.finished = True

    # Copy current screen image
    renderable = cmp.Renderable(scene.window.copy())
    position = cmp.Position()
    scene.next_scene.scene_state.world.create_entity(position, renderable)

    text = scene.scene_state.world.component_for_entity(dialog_menu_trigger_event.sign_ent_id, cmp.Sign).text

    scene.next_scene.scene_state.world.create_entity(renderable, position)
    menu_system = get_processor_instance(scene.next_scene, DialogMenuSystem)
    menu_system.create_new_text_box(text)

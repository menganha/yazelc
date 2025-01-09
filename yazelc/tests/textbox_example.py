import pygame

from event.events import InputEvent

pygame.init()

import zesper
from event.event_manager import EventManager

from yazelc.config import Config
from yazelc.resource_manager import ResourceManager
from yazelc.systems.dialog_menu_system import DialogMenuSystem
from yazelc.systems.render_system import RenderSystem
from yazelc.systems.delayed_entity_removal_system import DelayedEntityRemovalSystem
from yazelc.components import Sign
from yazelc.event.events import DialogTriggerEvent
from yazelc.keyboard import Keyboard, Button

# Colours
BACKGROUND = (255, 255, 255)


# The main function that controls the game
def main():
    config = Config.load_from_json('../settings.json')
    resource_manager = ResourceManager('../../assets')
    event_manager = EventManager()
    world = zesper.World()
    controller = Keyboard()

    resource_manager.add('Anonymous Pro.ttf')

    window = pygame.display.set_mode(config.window.resolution, pygame.SCALED, vsync=1)

    dialog_menu_system = DialogMenuSystem(config, resource_manager, event_manager)
    render_system = RenderSystem(window, config)
    removal_system = DelayedEntityRemovalSystem()
    world.add_processor(dialog_menu_system)
    world.add_processor(render_system)
    world.add_processor(removal_system)

    event_manager.subscribe_handler(dialog_menu_system)
    event_manager.subscribe_handler(removal_system)

    sign_ent_id = world.create_entity(Sign('A sample text'))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()

        controller.process_input()
        event_manager.dispatch_event(InputEvent(controller))

        if controller.is_button_down(Button.LEFT):
            event_manager.dispatch_event(DialogTriggerEvent(sign_ent_id))

        world.process()


if __name__ == '__main__':
    main()

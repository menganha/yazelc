import pygame

import settings as cfg
from yazelc import components as cmp
from yazelc import zesper
from yazelc.controller import Button
from yazelc.event.events import ChangeSceneEvent
from yazelc.event.events import InputEvent, RestartEvent, ResumeEvent

SURFACE_DEPTH = 2000  # Above everything else (1000 is the top map layer depth)
WIDTH = 130
TITLE_TEXT_POS_Y = 3
INITIAL_HEIGHT = 30
ROW_HEIGHT_INCREMENT = 10
ALPHA_INACTIVE = 150
INITIAL_ITEM_POS_Y = 25
ITEM_SEP_Y = 12
BG_COLOR = pygame.Color(0, 0, 0, 90)
MENU_FONT_ID = 'MENU'


def create_death_menu(world: zesper.World):
    title = ''
    items = ['Save and Continue', 'Quit']
    font = world.resource_manager.get_font(MENU_FONT_ID)
    menu_type = cmp.MenuType.DEATH
    world.create_entity(get_components(title, items, font, menu_type))


def create_pause_menu(world: zesper.World):
    title = 'PAUSE'
    items = ['Continue', 'Quit']
    font = world.resource_manager.get_font(MENU_FONT_ID)
    menu_type = cmp.MenuType.PAUSE
    world.create_entity(get_components(title, items, font, menu_type))


def handle_menu_input(input_event: InputEvent, ent_id: int, menu: cmp.Menu, world: zesper.World):
    if menu.menu_type == cmp.MenuType.DEATH:
        _handle_death_menu_input(input_event, ent_id, menu, world)
    elif menu.menu_type == cmp.MenuType.PAUSE:
        _handle_pause_menu_input(input_event, ent_id, menu, world)
    elif menu.menu_type == cmp.MenuType.START:
        _handle_start_game_menu_input(input_event, ent_id, menu, world)


def get_components(title: str, items: list[str], font, menu_type: cmp.MenuType) -> tuple[cmp.Menu, cmp.Position, cmp.Renderable]:
    height = INITIAL_HEIGHT + len(items) * ROW_HEIGHT_INCREMENT
    menu = cmp.Menu(menu_type, title, items, font)
    surface = pygame.Surface((WIDTH, height), pygame.SRCALPHA)
    menu_pos_x = round((cfg.RESOLUTION.x - WIDTH) // 2)
    menu_pos_y = round((cfg.RESOLUTION.y - height) // 2)

    position = cmp.Position(menu_pos_x, menu_pos_y, absolute=True)
    renderable = cmp.Renderable(image=surface, depth=SURFACE_DEPTH)

    _refresh_menu_renderable(menu, surface)
    return menu, position, renderable


def _handle_start_game_menu_input(input_event: InputEvent, ent_id, menu: cmp.Menu, world: zesper.World):
    menu_ = _update_menu(input_event, ent_id, menu, world)
    if input_event.controller.is_button_pressed(Button.A) or input_event.controller.is_button_pressed(Button.START):
        if menu_.item_idx_y == 0:
            world.event_queue.add(ChangeSceneEvent('gameplay'))
        elif menu_.item_idx_y == 1:
            pass
        elif menu_.item_idx_y == 2:
            quit_event = pygame.event.Event(pygame.QUIT)
            pygame.event.post(quit_event)


def _handle_death_menu_input(input_event: InputEvent, ent_id, menu: cmp.Menu, world: zesper.World):
    menu_ = _update_menu(input_event, ent_id, menu, world)
    if input_event.controller.is_button_pressed(Button.A):
        if menu_.item_idx_y == 0:
            world.delete_entity(ent_id)
            world.event_queue.add(RestartEvent())
        elif menu_.item_idx_y == 1:
            quit_event = pygame.event.Event(pygame.QUIT)
            pygame.event.post(quit_event)


def _handle_pause_menu_input(input_event: InputEvent, ent_id, menu: cmp.Menu, world: zesper.World):
    menu_ = _update_menu(input_event, ent_id, menu, world)
    if input_event.controller.is_button_pressed(Button.A):
        if menu_.item_idx_y == 0:
            world.delete_entity(ent_id)
            world.event_queue.add(ResumeEvent())
        elif menu_.item_idx_y == 1:
            quit_event = pygame.event.Event(pygame.QUIT)
            pygame.event.post(quit_event)
    elif input_event.controller.is_button_pressed(Button.START):
        world.event_queue.add(ResumeEvent())
        world.delete_entity(ent_id)


def _refresh_menu_renderable(menu: cmp.Menu, surface: pygame.Surface):
    """ Updates the menu image with the current selection """
    surface.fill(BG_COLOR)
    menu.font.render_text_at(menu.title, surface, pos_y=TITLE_TEXT_POS_Y)
    pos_y = INITIAL_ITEM_POS_Y
    for idx, text in enumerate(menu.items):
        alpha = None if idx == menu.item_idx_y else ALPHA_INACTIVE
        menu.font.render_text_at(text, surface, pos_y=pos_y, alpha=alpha)
        pos_y += ITEM_SEP_Y


def _update_menu(input_event: InputEvent, ent_id: int, menu: cmp.Menu, world: zesper.World) -> cmp.Menu:
    """ Updates the menu's selected item depending on the input """

    direction_x = - input_event.controller.is_button_pressed(Button.LEFT) + input_event.controller.is_button_pressed(Button.RIGHT)
    direction_y = - input_event.controller.is_button_pressed(Button.UP) + input_event.controller.is_button_pressed(Button.DOWN)

    menu.item_idx_x += direction_x
    menu.item_idx_y += direction_y

    menu.item_idx_x = max(0, min(len(menu) - 1, menu.item_idx_x))
    menu.item_idx_y = max(0, min(len(menu) - 1, menu.item_idx_y))

    if direction_x | direction_y:
        image_surface = world.component_for_entity(ent_id, cmp.Renderable).image
        _refresh_menu_renderable(menu, image_surface)
    return menu

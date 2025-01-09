import pygame

from yazelc import zesper
from yazelc.components import Sign, Renderable, Position, Menu, TextBox
from yazelc.config import Config
from yazelc.controller import Button
from yazelc.event.event_manager import EventManager
from yazelc.event.events import InputEvent, ResumeEvent, DialogTriggerEvent, PauseEvent, SoundTriggerEvent, SoundEndEvent
from yazelc.font import Font
from yazelc.menu import menu_box
from yazelc.resource_manager import ResourceManager


class DialogMenuSystem(zesper.Processor):
    """ Handles all text dialog (NPC and signs) and the context menus """

    def __init__(self, config: Config, resource_manager: ResourceManager, event_manager: EventManager):
        self.width = config.window.resolution.x
        self.height = config.text_box.height
        self.surface_depth = config.text_box.image_depth  # above everything else but below the pause menu
        self.x_margin = config.text_box.x_margin
        self.y_margin = config.text_box.y_margin
        self.extra_line_spacing = config.text_box.extra_line_spacing
        self.triangle_vertices: list[tuple[int, int]] = list()
        for shift in config.text_box.triangle_vertices_rel_pos:
            self.triangle_vertices.append((self.width - shift.x, self.height - shift.y))
        self.menu_pos_x = 0
        self.menu_pos_y = config.window.resolution.y - self.height
        self.scroll_sound_id = config.text_box.scroll_sound
        self.bgcolor = config.text_box.bgcolor
        self.font = Font(resource_manager.get_font(config.text_box.font.name), **config.text_box.font.properties)
        self.event_manager = event_manager

    def process(self):
        for _, (text_box, renderable) in self.world.get_components(TextBox, Renderable):
            if text_box.idle:
                continue

            if text_box.frame_tick < text_box.frame_delay:
                text_box.frame_tick += 1
                continue

            line_spacing = self.font.line_spacing + self.extra_line_spacing

            if text_box.index == 0:
                text_box.x_pos, text_box.y_pos = self.x_margin, self.font.line_spacing + self.y_margin

            if not self.font.fits_on_box(text_box.current_sentence(), self.width):
                text_box.y_pos += line_spacing
                text_box.x_pos = self.x_margin
                text_box.index_start = text_box.index

            if text_box.y_pos >= self.height - self.y_margin:
                self.add_triangle_signal(renderable.image)
                text_box.x_pos, text_box.y_pos = self.x_margin, self.font.line_spacing + self.y_margin
                text_box.index_start = text_box.index
                text_box.idle = True
                self.event_manager.event_queue.add(SoundEndEvent(self.scroll_sound_id))
                continue

            char_to_render = text_box.next_char()
            self.font.render_text_at(char_to_render, renderable.image, text_box.x_pos, text_box.y_pos)
            text_box.x_pos += self.font.advance
            text_box.index += 1
            text_box.frame_tick = 0

            if text_box.is_at_end():
                self.add_triangle_signal(renderable.image)
                text_box.idle = True
                self.event_manager.event_queue.add(SoundEndEvent(self.scroll_sound_id))

    def on_input(self, input_event: InputEvent):

        for entity, (text_box, renderable_) in self.world.get_components(TextBox, Renderable):
            if input_event.controller.is_button_pressed(Button.A) and text_box.idle:
                if text_box.is_at_end():
                    self.world.delete_entity(entity)
                    self.event_manager.event_queue.add(ResumeEvent())
                else:
                    text_box.idle = False
                    renderable_.image.fill(self.bgcolor)
                    self.event_manager.event_queue.add(SoundTriggerEvent(self.scroll_sound_id))

        # Handle Menus. TODO: Should we have a separate system to handle these??
        for entity, (menu, renderable_) in self.world.get_components(Menu, Renderable):
            menu_box.handle_menu_input(input_event, entity, menu, self.world)

    def on_dialog_trigger(self, dialog_trigger_event: DialogTriggerEvent):
        """ Generate a text box entity """

        text_box_entity_id = self.world.create_entity()
        background = pygame.Surface((self.width, self.height))
        background.fill(self.bgcolor)

        sign = self.world.component_for_entity(dialog_trigger_event.dialog_entity_id, Sign)
        self.world.add_component(text_box_entity_id, TextBox(sign.text))
        self.world.add_component(text_box_entity_id, Renderable(image=background, depth=self.surface_depth))
        self.world.add_component(text_box_entity_id, Position(self.menu_pos_x, self.menu_pos_y, absolute=True))

        self.event_manager.event_queue.add(PauseEvent())  # TODO: Remove this from here and pass it to the caller
        self.event_manager.event_queue.add(SoundTriggerEvent(self.scroll_sound_id))

    def add_triangle_signal(self, image: pygame.Surface):
        """ Creates an entity that signals when the dialog has finished being written onto the dialog screen """
        pygame.draw.polygon(image, self.font.fgcolor, self.triangle_vertices)

import pygame

from settings import Settings
from yazelc import zesper
from yazelc.components import Sign, Renderable, Position, TextBox
from yazelc.controller import Button
from yazelc.event.event_manager import ButtonDownEvent
from yazelc.event.events import eventclass, SoundTriggerEvent, SoundEndEvent
from yazelc.resource_manager import ResourceManager
from yazelc.utils.game_utils import IVec


@eventclass
class DialogMenuExitEvent:
    dialog_entity_id: int


@eventclass
class DialogMenuTriggerEvent:
    sign_ent_id: int


class DialogMenuSystem(zesper.Processor):
    """ Handles all text dialog (NPC and signs) and the context menus """

    def __init__(self, config: Settings, world: zesper.World, resource_manager: ResourceManager):
        super().__init__()
        self.world = world
        self.width = config.window.resolution.x
        self.height = config.text_box.height
        self.surface_depth = config.text_box.image_depth  # above everything else but below the pause menu
        self.x_margin = config.text_box.x_margin
        self.y_margin = config.text_box.y_margin
        self.extra_line_spacing = config.text_box.extra_line_spacing
        self.triangle_signal_vertices = config.text_box.triangle_signal_vertices
        self.rect_signal = config.text_box.rect_signal
        self.menu_pos_x = 0
        self.menu_pos_y = config.window.resolution.y - self.height
        self.scroll_sound_id = config.text_box.scroll_sound
        self.bgcolor = config.text_box.bgcolor
        self.font = resource_manager.font(config.text_box.font.name, **config.text_box.font.properties)

    def process(self):
        for _, (text_box, renderable) in self.world.get_components(TextBox, Renderable):

            if text_box.idle:
                continue

            if text_box.frame_tick < text_box.frame_delay:  # Wait (thi is how fast we type into the screen)
                text_box.frame_tick += 1
                continue

            line_spacing = self.font.height + self.extra_line_spacing

            if text_box.cursor == 0:
                text_box.x_pos, text_box.y_pos = self.x_margin, self.y_margin

            # If the next word doesn't fit try next line
            if self.font.get_width(text_box.current_sentence()) > (self.width - 2 * self.x_margin):
                text_box.y_pos += line_spacing
                text_box.x_pos = self.x_margin
                text_box.cursor_start = text_box.cursor

            # If the text has filled the box draw triangle signal
            if text_box.y_pos >= self.height - self.y_margin - self.font.height:
                self.add_triangle_signal(renderable.image)
                text_box.x_pos, text_box.y_pos = self.x_margin, self.y_margin
                text_box.cursor_start = text_box.cursor
                text_box.idle = True
                self.event_queue.add(SoundEndEvent(self.scroll_sound_id))
                continue

            # Render next character
            char_to_render = text_box.next_char()
            target_pos = IVec(text_box.x_pos, text_box.y_pos)
            self.font.render_to(renderable.image, target_pos, char_to_render)
            text_box.x_pos += self.font.get_width(char_to_render)
            text_box.cursor += 1
            text_box.frame_tick = 0

            # If all text is written
            if text_box.is_at_end():
                self.add_square_signal(renderable.image)
                text_box.idle = True
                self.event_queue.add(SoundEndEvent(self.scroll_sound_id))

    def on_input(self, button_down_event: ButtonDownEvent):
        if button_down_event.button == Button.A:
            for entity, (text_box, renderable_) in self.world.get_components(TextBox, Renderable):
                if text_box.idle:
                    if text_box.is_at_end():
                        self.world.delete_entity(entity)
                        self.event_queue.add(DialogMenuExitEvent(entity))
                    else:
                        text_box.idle = False
                        renderable_.image.fill(self.bgcolor)
                        self.event_queue.add(SoundTriggerEvent(self.scroll_sound_id))

        # # Handle Menus. TODO: Should we have a separate system to handle these??
        # for entity, (menu, renderable_) in self.world.get_components(Menu, Renderable):
        #     menu_box.handle_menu_input(input_event, entity, menu, self.world)

    # TODO: maybe do not trigger it on event, simply call it. Do we use it this way anywhere else?
    def on_dialog_trigger(self, dialog_trigger_event: DialogMenuTriggerEvent):
        """ Generates a text box entity """
        text_box_entity_id = self.world.create_entity()

        background = pygame.Surface((self.width, self.height))
        background.fill(self.bgcolor)

        sign = self.world.component_for_entity(dialog_trigger_event.sign_ent_id, Sign)
        self.world.add_component(text_box_entity_id, TextBox(sign.text))
        self.world.add_component(text_box_entity_id, Renderable(image=background, depth=self.surface_depth))
        self.world.add_component(text_box_entity_id, Position(self.menu_pos_x, self.menu_pos_y))

        self.event_queue.add(SoundTriggerEvent(self.scroll_sound_id))

    def add_triangle_signal(self, image: pygame.Surface):
        """ Creates an entity that signals when the dialog has finished being written onto the dialog screen """
        pygame.draw.polygon(image, self.font.color, self.triangle_signal_vertices)

    def add_square_signal(self, image: pygame.Surface):
        """ Creates an entity that signals when the dialog has finished being written onto the dialog screen """
        pygame.draw.rect(image, self.font.color, self.rect_signal)

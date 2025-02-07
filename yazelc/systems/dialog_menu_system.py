import pygame

from yazelc import zesper
from yazelc.components import Renderable, TextBox
from yazelc.event.events import eventclass, SoundEndEvent
from yazelc.resource_manager import ResourceManager
from yazelc.settings import Settings
from yazelc.utils.game_utils import IVec


@eventclass
class DialogTriggerEvent:
    sign_ent_id: int


class DialogMenuSystem(zesper.Processor):
    """ Handles all text dialog (NPC and signs) and the context menus """

    def __init__(self, config: Settings, world: zesper.World, resource_manager: ResourceManager):
        super().__init__()
        # TODO: Remove all this garbage that is not needed in the processing of the data but just to set a new entitiy.
        #       This can go on the DialogScene class
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


    def add_triangle_signal(self, image: pygame.Surface):
        """ Creates an entity that signals when the dialog has finished being written onto the dialog screen """
        pygame.draw.polygon(image, self.font.color, self.triangle_signal_vertices)

    def add_square_signal(self, image: pygame.Surface):
        """ Creates an entity that signals when the dialog has finished being written onto the dialog screen """
        pygame.draw.rect(image, self.font.color, self.rect_signal)

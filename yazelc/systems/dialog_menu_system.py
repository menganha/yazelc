from dataclasses import dataclass

import pygame

from yazelc import zesper
from yazelc.components import Renderable, Position
from yazelc.controller import ButtonPressedEvent, Button
from yazelc.event.events import eventclass, SoundEndEvent, SoundTriggerEvent
from yazelc.resource_manager import ResourceManager
from yazelc.settings import TextBoxConfig
from yazelc.utils.game_utils import IVec
from yazelc.utils.timer import Timer


@eventclass
class DialogEndEvent:
    text_box_entity: int


@eventclass
class CreateTextBoxEvent:
    text: str


@dataclass
class SignalSymbol:
    """ Signal at the end of the text printing"""
    ent_id: int
    surface: pygame.Surface


@dataclass
class TextBox:
    """ Text boxes used for showing the dialog """
    text: str = ''
    cursor: int = 0  # Index of the char at which the rendered text is actually in
    line_start: int = 0  # Index of the text char at which the current line starts
    x_pos: int = 0
    y_pos: int = 0

    def next_char(self) -> str:
        return self.text[self.cursor]

    def is_at_end(self) -> bool:
        return self.cursor >= len(self.text)

    def current_sentence(self) -> str:
        """ Gives the sentence until the word (including it) at which the index is """
        sentence = self.text[self.line_start:self.cursor + 1]
        n_words = len(sentence.rstrip().split(' '))
        words = self.text[self.line_start:].split(' ')[:n_words]
        return ' '.join(words)


class DialogMenuSystem(zesper.Processor):
    """ Handles all text dialog (NPC and signs) and the context menus """

    def __init__(self, config: TextBoxConfig, world: zesper.World, resource_manager: ResourceManager):
        super().__init__()
        self.world = world
        self.config = config
        self.font = resource_manager.font(config.font.name, **config.font.properties)

        # the triangle indicator
        max_x = max(ele.x for ele in config.triangle_signal_vertices)
        min_x = min(ele.x for ele in config.triangle_signal_vertices)
        max_y = max(ele.y for ele in config.triangle_signal_vertices)
        min_y = min(ele.y for ele in config.triangle_signal_vertices)
        size_of_box_containing_triangle = (max_x - min_x + 1, max_y - min_y + 1)
        triangle_sur = pygame.Surface(size_of_box_containing_triangle)
        triangle_sur.fill(config.bgcolor)
        offset_vertices = [(vec.x - min_x, vec.y - min_y) for vec in self.config.triangle_signal_vertices]
        pygame.draw.polygon(triangle_sur, self.font.color, offset_vertices)
        position = min_x, min_y
        triangle_ent = self.world.create_entity(Position(*position))
        self.triangle = SignalSymbol(triangle_ent, triangle_sur)

        # the square indicator
        square_sur = pygame.Surface(self.config.rect_signal.size)
        square_sur.fill(config.bgcolor)
        offset_rect = self.config.rect_signal.copy()
        offset_rect.topleft = (0, 0)
        pygame.draw.rect(square_sur, self.font.color, offset_rect)
        square_ent = self.world.create_entity(Position(*config.rect_signal.topleft))
        self.square = SignalSymbol(square_ent, square_sur)

        self.blinking_timer = Timer(config.blinking)

        # the text box
        self.text_box = TextBox()
        self.text_box_entity = self.world.create_entity(Position(*self.config.rect.topleft))
        self.idle = True
        self.typewriter_timer = Timer(1)

    def process(self):

        if self.idle or self.text_box.is_at_end():  # or is at end?
            self.blinking_timer.tick()
            if self.blinking_timer.has_finished():
                signal = self.triangle if self.idle else self.square
                if self.world.has_component(signal.ent_id, Renderable):
                    self.world.remove_component(signal.ent_id, Renderable)
                else:
                    self.world.add_component(signal.ent_id, Renderable(signal.surface, depth=self.config.depth + 1))
                self.blinking_timer.reset()

        elif self.typewriter_timer.has_finished():

            line_spacing = self.font.height + self.config.extra_line_spacing

            if self.text_box.cursor == 0:
                self.text_box.x_pos, self.text_box.y_pos = self.config.margin

            # If the next word doesn't fit try next line
            if self.font.get_width(self.text_box.current_sentence()) > (self.config.rect.width - 2 * self.config.margin.x):
                self.text_box.y_pos += line_spacing
                self.text_box.x_pos = self.config.margin.x
                self.text_box.line_start = self.text_box.cursor

                # If the text doesn't fit the box then draw triangle signal and wait for event
                if self.text_box.y_pos >= self.config.rect.height - self.config.margin.y - self.font.height:
                    self.world.add_component(self.triangle.ent_id, Renderable(self.triangle.surface, depth=self.config.depth + 1))
                    self.text_box.x_pos, self.text_box.y_pos = self.config.margin
                    self.text_box.line_start = self.text_box.cursor
                    self.idle = True
                    self.event_queue.add(SoundEndEvent(self.config.scroll_sound))
                    self.blinking_timer.reset()

            else:  # Render next character
                char_to_render = self.text_box.next_char()
                target_pos = IVec(self.text_box.x_pos, self.text_box.y_pos)
                renderable = self.world.component_for_entity(self.text_box_entity, Renderable)
                self.font.render_to(renderable.image, target_pos, char_to_render)
                self.text_box.x_pos += self.font.get_width(char_to_render)
                self.text_box.cursor += 1

            # If all text is written
            if self.text_box.is_at_end():
                self.world.add_component(self.square.ent_id, Renderable(self.square.surface, depth=self.config.depth + 1))
                self.event_queue.add(SoundEndEvent(self.config.scroll_sound))
                self.blinking_timer.reset()
        else:
            self.typewriter_timer.tick()

    def on_button_pressed(self, button_down_event: ButtonPressedEvent):
        if button_down_event.button == Button.A:
            if self.text_box.is_at_end():
                self.event_queue.add(DialogEndEvent(self.text_box_entity))
            elif self.idle:
                self.idle = False
                renderable = self.world.component_for_entity(self.text_box_entity, Renderable)
                renderable.image.fill(self.config.bgcolor)
                if self.world.has_component(self.triangle.ent_id, Renderable):
                    self.world.remove_component(self.triangle.ent_id, Renderable)
                self.event_queue.add(SoundTriggerEvent(self.config.scroll_sound))

    def on_create_textbox(self, create_text_box_event: CreateTextBoxEvent):
        self.text_box = TextBox(create_text_box_event.text)
        self.idle = False
        background = pygame.Surface(self.config.rect.size)
        background.fill(self.config.bgcolor)
        renderable = Renderable(image=background, depth=self.config.depth)
        self.world.add_component(self.text_box_entity, renderable)

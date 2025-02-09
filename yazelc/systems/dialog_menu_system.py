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
    pass


@dataclass()
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

        self.blinking_timer = Timer(config.blinking)
        self.signal_visible = False

        self.text_box = TextBox()
        self.background = pygame.Surface(config.rect.size)
        self.background.fill(config.bgcolor)
        self.text_box_image = None
        self.idle: bool = False
        self.typing_delay_time = 1
        self.typing_delay_counter = 0

        self.ent_id = -1

    def process(self):

        if not self.world.entity_exists(self.ent_id):
            return
        elif self.idle:
            self.blinking_timer.tick()
            if self.blinking_timer.has_finished():
                color = self.font.color if self.signal_visible else self.config.bgcolor
                if self.text_box.is_at_end():
                    pygame.draw.rect(self.background, color, self.config.rect_signal)
                else:
                    pygame.draw.polygon(self.background, color, self.config.triangle_signal_vertices)
                self.signal_visible = not self.signal_visible
                self.blinking_timer.reset()

        elif self.typing_delay_counter >= self.typing_delay_time:

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
                    self.text_box.x_pos, self.text_box.y_pos = self.config.margin
                    self.text_box.line_start = self.text_box.cursor
                    self.idle = True
                    self.event_queue.add(SoundEndEvent(self.config.scroll_sound))
                    pygame.draw.polygon(self.background, self.font.color, self.config.triangle_signal_vertices)
                    self.signal_visible = True
                    self.blinking_timer.reset()

            else:  # Render next character
                char_to_render = self.text_box.next_char()
                target_pos = IVec(self.text_box.x_pos, self.text_box.y_pos)
                self.font.render_to(self.background, target_pos, char_to_render)
                self.text_box.x_pos += self.font.get_width(char_to_render)
                self.text_box.cursor += 1

            # If all text is written
            if self.text_box.is_at_end():
                pygame.draw.rect(self.background, self.font.color, self.config.rect_signal)
                self.signal_visible = True
                self.event_queue.add(SoundEndEvent(self.config.scroll_sound))
                self.blinking_timer.reset()
                self.idle = True
        else:
            self.typing_delay_counter += 1

    def on_button_pressed(self, button_down_event: ButtonPressedEvent):
        if button_down_event.button == Button.A:
            if self.text_box.is_at_end():
                if self.world.has_component(self.ent_id, Renderable):
                    self.world.remove_component(self.ent_id, Renderable)
                self.event_queue.add(DialogEndEvent())
            elif self.idle:
                self.idle = False
                self.background.fill(self.config.bgcolor)
                self.event_queue.add(SoundTriggerEvent(self.config.scroll_sound))

    def create_new_text_box(self, text: str):
        position = Position(*self.config.rect.topleft)
        renderable = Renderable(image=self.background, depth=self.config.depth)
        self.text_box.text = text
        self.idle = False
        self.ent_id = self.world.create_entity(renderable, position)

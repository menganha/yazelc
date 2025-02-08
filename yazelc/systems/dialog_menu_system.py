from dataclasses import dataclass

import pygame

from yazelc import zesper
from yazelc.components import Renderable, Position, TextBox
from yazelc.controller import ButtonPressedEvent, Button
from yazelc.event.events import eventclass, SoundEndEvent, SoundTriggerEvent
from yazelc.resource_manager import ResourceManager
from yazelc.settings import TextBoxConfig
from yazelc.utils.game_utils import IVec
from yazelc.utils.timer import Timer


@eventclass
class DialogEndEvent:
    pass


@dataclass
class SignalSymbol:
    """ Signal at the end of the text printing"""
    position: Position
    surface: pygame.Surface


class DialogMenuSystem(zesper.Processor):
    """ Handles all text dialog (NPC and signs) and the context menus """

    def __init__(self, config: TextBoxConfig, world: zesper.World, resource_manager: ResourceManager):
        super().__init__()
        self.world = world
        self.config = config
        self.font = resource_manager.font(config.font.name, **config.font.properties)

        self.blinking_timer = Timer(config.blinking)
        self.signal_visible = False

    def process(self):

        for ent, (text_box, renderable) in self.world.get_components(TextBox, Renderable):

            if text_box.idle:
                self.blinking_timer.tick()
                if self.blinking_timer.has_finished():
                    color = self.font.color if self.signal_visible else self.config.bgcolor
                    if text_box.is_at_end():
                        pygame.draw.rect(renderable.image, color, self.config.rect_signal)
                    else:
                        pygame.draw.polygon(renderable.image, color, self.config.triangle_signal_vertices)
                    self.signal_visible = not self.signal_visible
                    self.blinking_timer.reset()

            elif text_box.counter >= text_box.typing_time:

                line_spacing = self.font.height + self.config.extra_line_spacing

                if text_box.cursor == 0:
                    text_box.x_pos, text_box.y_pos = self.config.margin

                # If the next word doesn't fit try next line
                if self.font.get_width(text_box.current_sentence()) > (self.config.rect.width - 2 * self.config.margin.x):
                    text_box.y_pos += line_spacing
                    text_box.x_pos = self.config.margin.x
                    text_box.line_start = text_box.cursor

                    # If the text doesn't fit the box then draw triangle signal and wait for event
                    if text_box.y_pos >= self.config.rect.height - self.config.margin.y - self.font.height:
                        text_box.x_pos, text_box.y_pos = self.config.margin
                        text_box.line_start = text_box.cursor
                        text_box.idle = True
                        self.event_queue.add(SoundEndEvent(self.config.scroll_sound))
                        pygame.draw.polygon(renderable.image, self.font.color, self.config.triangle_signal_vertices)
                        self.signal_visible = True
                        self.blinking_timer.reset()

                else:  # Render next character
                    char_to_render = text_box.next_char()
                    target_pos = IVec(text_box.x_pos, text_box.y_pos)
                    self.font.render_to(renderable.image, target_pos, char_to_render)
                    text_box.x_pos += self.font.get_width(char_to_render)
                    text_box.cursor += 1

                # If all text is written
                if text_box.is_at_end():
                    pygame.draw.rect(renderable.image, self.font.color, self.config.rect_signal)
                    self.signal_visible = True
                    self.event_queue.add(SoundEndEvent(self.config.scroll_sound))
                    self.blinking_timer.reset()
                    text_box.idle = True
            else:
                text_box.counter += 1

    def on_button_pressed(self, button_down_event: ButtonPressedEvent):
        if button_down_event.button == Button.A:
            for entity, (text_box, renderable) in self.world.get_components(TextBox, Renderable):
                if text_box.is_at_end():
                    self.world.delete_entity(entity)
                    self.event_queue.add(DialogEndEvent())
                elif text_box.idle:
                    text_box.idle = False
                    renderable.image.fill(self.config.bgcolor)
                    self.event_queue.add(SoundTriggerEvent(self.config.scroll_sound))

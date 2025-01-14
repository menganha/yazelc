from collections import defaultdict
from collections.abc import Callable
from types import MethodType
from typing import Any, TypeVar
from weakref import ref, WeakMethod

import pygame

from yazelc.controller import Controller, Button
from yazelc.event.events import eventclass
from yazelc.zesper import World

_EVENT = TypeVar('_EVENT')  # used for the static type checker for admitting any subclass
_EVENT_TYPE = type[_EVENT]


@eventclass
class CloseWindowEvent:
    pass  # TODO: Eventually move it to a window class


@eventclass
class ButtonDownEvent:
    button: Button  # TODO: Eventually move it to a controller class


@eventclass
class ButtonPressedEvent:
    button: Button  # TODO: Eventually move it to a controller class


@eventclass
class ButtonReleasedEvent:
    button: Button  # TODO: Eventually move it to a controller class

class EventManager:
    """
    Event manager that consumes (publish or broadcast) all collected events in one go
    Uses a "defaultdict" for subscriber storage to initialize a set when using a new (missing) key in the dict.
    Additionally, includes the event queue of all accumulated events
    """

    def __init__(self):
        self.subscribers = defaultdict(set)

    def process_all_events(self, controller: Controller = None, world: World = None):
        """ Dispatches all the game events and let the handlers process them """

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.trigger_event(CloseWindowEvent())

        if controller:
            controller.update()
            for button in Button:
                if controller.is_button_down(button):
                    self.trigger_event(ButtonDownEvent(button))
                elif controller.is_button_pressed(button):
                    self.trigger_event(ButtonPressedEvent(button))
                elif controller.is_button_released(button):
                    self.trigger_event(ButtonReleasedEvent(button))

        if world:
            for processor in world.get_all_processors():
                while processor.event_queue:
                    event = processor.event_queue.popleft()
                    self.trigger_event(event)
                processor.event_queue.process_delayed_events()

    def subscribe(self, event_type: _EVENT_TYPE, *handlers: Callable[[_EVENT], None]):
        """ Subscribe handler methods to event type """
        event_name = event_type.__name__.lower()
        for hdl in handlers:
            self._subscribe_handler_method(event_name, hdl)

    def subscribe_handler(self, instance: Any):
        """
        Subscribe all bound methods of type if they have the right name format: on_{event type}.
        Underscores after the "on_" are ignored.
        """
        for event_name, handler_method in self._relevant_methods(instance):
            self._subscribe_handler_method(event_name, handler_method)

    def trigger_event(self, event: _EVENT):
        event_name = type(event).__name__.lower()
        for listener in self.subscribers[event_name]:
            listener()(event)

    def remove_handler_method(self, event_type: _EVENT_TYPE, handler: Callable[[_EVENT], None]):
        event_name = event_type.__name__.lower()
        self._remove_handler(event_name, handler)

    def remove_handler(self, instance: Any):
        for event_name, handler_method in self._relevant_methods(instance):
            self._remove_handler(event_name, handler_method)

    def remove_all_handlers(self, event_type: _EVENT_TYPE = None):
        if event_type:
            event_name = event_type.__name__.lower()
            self.subscribers.pop(event_name, None)
        else:
            self.subscribers = defaultdict(set)

    # TODO: Remove this. It is ugly and unexpected to automatically add methods to be handlers.
    #   Try to use the decorator approach similar to pyglet
    @staticmethod
    def _relevant_methods(instance: Any) -> iter:
        """ Returns the relevant method of the instance which can be subscribed """
        for attribute_name in vars(type(instance)):
            attribute = getattr(instance, attribute_name)
            if callable(attribute) and attribute_name.startswith('on_'):
                event_name = attribute_name.replace('on_', '').replace('_', '').lower() + 'event'
                yield event_name, attribute

    def _subscribe_handler_method(self, event_name: str, handler_method: Callable[[_EVENT], None]):
        """ Subscribe handler method to event type """
        reference_type = self._reference_type(handler_method)
        callback_on_garbage_collection = self._make_callback(event_name)
        self.subscribers[event_name].add(reference_type(handler_method, callback_on_garbage_collection))

    def _remove_handler(self, event_name: str, handler: Callable[[_EVENT], None]):
        reference_type = self._reference_type(handler)
        handler_reference = reference_type(handler)
        if handler_reference not in self.subscribers.get(event_name, []):
            return

        self.subscribers[event_name].remove(handler_reference)

        if not self.subscribers[event_name]:
            self.subscribers.pop(event_name)

    def _make_callback(self, event_name: str):
        """ Creates a callback to remove dead handlers """

        def callback(weak_method):
            self.subscribers[event_name].remove(weak_method)
            if not self.subscribers[event_name]:
                self.subscribers.pop(event_name)

        return callback

    @staticmethod
    def _reference_type(handler: Callable) -> Callable:
        if isinstance(handler, MethodType):
            reference_type = WeakMethod
        else:
            reference_type = ref
        return reference_type

import logging
from collections import defaultdict
from collections.abc import Callable
from types import MethodType
from typing import Any, TypeVar
from weakref import ref, WeakMethod

import pygame

from yazelc.controller import Controller, Button, ButtonDownEvent, ButtonReleasedEvent, ButtonPressedEvent
from yazelc.event.events import eventclass
from yazelc.zesper import Processor

_EVENT = TypeVar('_EVENT')  # used for the static type checker for admitting any subclass
_EVENT_TYPE = type[_EVENT]

logger = logging.getLogger(__name__)


@eventclass
class CloseWindowEvent:
    pass  # TODO: Eventually move it to a window class


class EventManager:
    """
    Event manager that consumes (publish or broadcast) all collected events. Handler of events can also be registered.
    The handlers are stored as weak references which are removed from the list of handlers once they are garbage
    collected
    Uses a "defaultdict" for subscriber storage to initialize a set when using a new (missing) key in the dict.
    """

    def __init__(self):
        self.subscribers = defaultdict(set)

    def process_all_events(self, controller: Controller = None, list_processors: list[Processor] = None):
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

        if list_processors:
            for processor in list_processors:
                while processor.event_queue:
                    event = processor.event_queue.popleft()
                    self.trigger_event(event)
                processor.event_queue.process_delayed_events()

    def subscribe(self, event_type: _EVENT_TYPE, *handlers: Callable[[_EVENT], None]):
        """ Subscribe handler methods to event type """
        event_name = event_type.__name__.lower()
        for hdl in handlers:
            reference_type = self._reference_type(hdl)
            callback_on_garbage_collection = self._make_callback(event_name)
            self.subscribers[event_name].add(reference_type(hdl, callback_on_garbage_collection))

    def trigger_event(self, event: _EVENT):
        event_name = type(event).__name__.lower()
        for listener in self.subscribers[event_name]:
            listener()(event)

    def remove_handler_for_event(self, event_type: _EVENT_TYPE, handler: Callable[[_EVENT], None]):
        event_name = event_type.__name__.lower()
        self._remove_handler(event_name, handler)

    def remove_handlers_for_instance(self, instance: Any):
        """ """
        raise NotImplementedError('Not correctly implemented yet')
        # for event_name, handler_method in self._relevant_methods(instance):
        #     self._remove_handler(event_name, handler_method)

    def remove_handlers(self, event_type: _EVENT_TYPE = None):
        """ If event type is not specified then it removes all handler"""
        if event_type:
            event_name = event_type.__name__.lower()
            self.subscribers.pop(event_name, None)
        else:
            self.subscribers = defaultdict(set)

    def _remove_handler(self, event_name: str, handler: Callable[[_EVENT], None]):
        reference_type = self._reference_type(handler)
        handler_reference = reference_type(handler)
        if handler_reference not in self.subscribers.get(event_name, []):
            return

        self.subscribers[event_name].remove(handler_reference)

        if not self.subscribers[event_name]:
            self.subscribers.pop(event_name)

    def _make_callback(self, event_name: str):
        """ Creates a callback to remove dead handlers, i.e., when the garbage collector is about to eliminate them """

        def callback(weak_ref_function):
            logger.info(
                f'Function {weak_ref_function} is about to be garbage collected. '
                f'Removing from the handlers list of the event manager for event "{event_name}"'
            )
            self.subscribers[event_name].remove(weak_ref_function)
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

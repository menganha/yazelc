import functools
import logging
from collections import defaultdict
from collections.abc import Callable
from types import MethodType
from typing import TypeVar, ParamSpec
from weakref import WeakMethod

import pygame

from yazelc.controller import Controller, Button, ButtonDownEvent, ButtonReleasedEvent, ButtonPressedEvent
from yazelc.event.event_queue import EventQueue
from yazelc.event.events import eventclass

_EVENT = TypeVar('_EVENT')  # used for the static type checker for admitting any subclass
_P = ParamSpec('_P')

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

    def process_system_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.trigger_event(CloseWindowEvent())

    def process_controller(self, controller: Controller):
        controller.update()
        for button in Button:
            if controller.is_button_down(button):
                self.trigger_event(ButtonDownEvent(button))

            if controller.is_button_pressed(button):
                self.trigger_event(ButtonPressedEvent(button))
            elif controller.is_button_released(button):
                self.trigger_event(ButtonReleasedEvent(button))

    def process_queue(self, event_queue: EventQueue):
        while event_queue:
            event = event_queue.popleft()
            self.trigger_event(event)
        event_queue.process_delayed_events()

    def subscribe(self, event_type: type[_EVENT], handler: Callable[[..., _EVENT], None] | Callable[[_EVENT], None], *args):
        """ Subscribe handler methods to event type """
        event_name = event_type.__name__.lower()
        if isinstance(handler, MethodType):
            callback_on_garbage_collection = self._make_callback(event_name)
            weak_method = WeakMethod(handler, callback_on_garbage_collection)
            self.subscribers[event_name].add(weak_method)
        else:
            # No need to remove dead handlers are these are raw module level functions, never garbage collected
            function = functools.partial(handler, *args)
            self.subscribers[event_name].add(function)

    def trigger_event(self, event: _EVENT):
        event_name = type(event).__name__.lower()
        for listener in self.subscribers[event_name]:
            if isinstance(listener, WeakMethod):
                listener()(event)
            else:
                listener(event)

    def remove_handler_for_event(self, event_type: type[_EVENT], handler: Callable[[_EVENT], None]):
        event_name = event_type.__name__.lower()
        for listener in self.subscribers.get(event_name, []):
            if isinstance(listener, WeakMethod):
                func = listener()
            else:
                func = listener.func
            if handler == func:
                self.subscribers[event_name].remove(listener)
                if not self.subscribers[event_name]:
                    self.subscribers.pop(event_name)
                break
        else:
            logger.info(f'listener {repr(handler)} was not found in subscriber list')

    def remove_handlers(self, event_type: type[_EVENT] = None):
        """ If event type is not specified then it removes all handler"""
        if event_type:
            event_name = event_type.__name__.lower()
            self.subscribers.pop(event_name, None)
        else:
            self.subscribers = defaultdict(set)

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

# TODO: All below are not used actively anymore. Consider removing them!!
#     def remove_handlers_for_instance(self, instance: Any):
#         """ """
#         raise NotImplementedError('Not correctly implemented yet')
#         # for event_name, handler_method in self._relevant_methods(instance):
#         #     self._remove_handler(event_name, handler_method)
#
#     def _remove_handler(self, event_name: str, handler: Callable[[_EVENT], None]):
#         reference_type = self._reference_type(handler)
#         handler_reference = reference_type(handler)
#         if handler_reference not in self.subscribers.get(event_name, []):
#             return
#
#         self.subscribers[event_name].remove(handler_reference)
#
#         if not self.subscribers[event_name]:
#             self.subscribers.pop(event_name)
#
#
#     @staticmethod
#     def _reference_type(handler: Callable) -> Callable:
#         if isinstance(handler, MethodType):
#             reference_type = WeakMethod
#         else:
#             reference_type = ref
#         return reference_type

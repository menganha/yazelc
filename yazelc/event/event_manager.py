from collections import defaultdict
from collections import deque
from collections.abc import Callable
from types import MethodType
from typing import Any
from typing import TypeVar
from weakref import ref, WeakMethod

from yazelc.utils.timer import Timer

_EVENT = TypeVar('_EVENT')  # used for the static type checker for admitting any subclass
_EVENT_TYPE = type[_EVENT]


class EventQueue:

    def __init__(self):
        self._event_queue: deque[Any] = deque()  # collects all events to be fired on the next frame
        self._event_buffer: list[Any] = list()  # collects events with delays
        self._buffer_delays: dict[int, Timer] = dict()

    def add(self, event: Any, frames_delay: int = 0):
        if frames_delay:
            self._event_buffer.append(event)
            self._buffer_delays[id(event)] = Timer(frames_delay)
        else:
            self._event_queue.append(event)

    def popleft(self) -> Any:
        return self._event_queue.popleft()

    def __bool__(self):
        return bool(self._event_queue)

    def process_delayed_events(self):
        """
        Removes one frame of waiting from the delay of the events in the buffer queue.
        If the frame delay reaches zero then it adds the event to the main queue
        """
        events_to_add = list()
        for event in self._event_buffer:
            timer = self._buffer_delays[id(event)]
            timer.tick()
            if timer.has_finished():
                events_to_add.append(event)
        self._event_queue.extend(events_to_add)
        for event in events_to_add:
            self._event_buffer.remove(event)
            self._buffer_delays.pop(id(event))

    def clear(self):
        self._event_queue.clear()
        self._event_buffer.clear()


class EventManager:
    """
    Event manager that consumes (publish or broadcast) all collected events in one go
    Uses a "defaultdict" for subscriber storage to initialize a set when using a new (missing) key in the dict.
    Additionally, includes the event queue of all accumulated events
    """

    def __init__(self):
        self.subscribers = defaultdict(set)
        self.event_queue = EventQueue()

    def dispatch_queue_events(self):
        """ Process all events from the queue """
        while self.event_queue:
            event = self.event_queue.popleft()
            self.dispatch_event(event)
        self.event_queue.process_delayed_events()

    def subscribe_handler_method(self, event_type: _EVENT_TYPE, handler_method: Callable[[_EVENT], None]):
        """ Subscribe handler method to event type """
        event_name = event_type.__name__.lower()
        self._subscribe_handler_method(event_name, handler_method)

    def subscribe_handler(self, instance: Any):
        """
        Subscribe all bound methods of type if they have the right name format: on_{event type}.
        Underscores after the "on_" are ignored.
        """
        for event_name, handler_method in self._relevant_methods(instance):
            self._subscribe_handler_method(event_name, handler_method)

    def dispatch_event(self, event: _EVENT):
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

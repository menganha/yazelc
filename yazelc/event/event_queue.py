from collections import deque
from typing import Any

from yazelc.utils.timer import Timer


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

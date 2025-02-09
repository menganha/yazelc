import gc
import unittest
from unittest.mock import Mock

from yazelc.event.event_manager import EventManager
from yazelc.event.events import eventclass


@eventclass
class MockPauseEvent:
    pass


@eventclass
class MockDeathEvent:
    pass


@eventclass
class MockCollisionEvent:
    pass


@eventclass
class PauseEvent:
    pass


class PauseClass:
    def on_pause(self, event: MockPauseEvent):
        pass


class DeathClass:
    def on_death(self, event: MockDeathEvent):
        pass


def regular_function(pause_event: PauseEvent):
    pass


def regular_function_more_arguments(arg1, arg2, pause_event: PauseEvent):
    pass

class TestEvent(unittest.TestCase):

    def setUp(self) -> None:
        self.event_manager = EventManager()
        instance_with_no_reference = PauseClass()  # It will be garbage collected after we go out of scope of the setup
        self.instance_with_reference = DeathClass()
        self.event_manager.subscribe(MockPauseEvent, instance_with_no_reference.on_pause)
        self.event_manager.subscribe(MockDeathEvent, self.instance_with_reference.on_death)
        self.event_manager.subscribe(MockCollisionEvent, self.instance_with_reference.on_death)

    def test_remove_one_handlers(self):
        self.event_manager.remove_handler_for_event(MockDeathEvent, self.instance_with_reference.on_death)
        self.assertTrue('mockdeathevent' not in self.event_manager.subscribers)
        self.assertTrue('mockcollisionevent' in self.event_manager.subscribers)

    def test_remove_all_handlers(self):
        self.event_manager.remove_handlers()
        self.assertFalse(self.event_manager.subscribers)

    def test_remove_all_handlers_of_one_event_type(self):
        self.event_manager.remove_handlers(MockCollisionEvent)
        self.assertFalse(self.event_manager.subscribers['mockcollisionevent'])
        self.assertTrue(self.event_manager.subscribers['mockdeathevent'])

    def test_weak_ref(self):
        gc.collect()
        self.assertTrue('mockpauseevent' not in self.event_manager.subscribers)
        self.assertTrue('mockdeathevent' in self.event_manager.subscribers)

    def test_dispatch_event(self):
        class MockEvent:
            pass

        event = MockEvent()
        mock_method_1 = Mock()
        mock_method_2 = Mock()
        mock_method_3 = Mock()
        self.event_manager.subscribe(MockEvent, mock_method_1)
        self.event_manager.subscribe(MockEvent, mock_method_2)
        self.event_manager.subscribe(MockEvent, mock_method_3, 'dummy_arg', 'dummy_arg2')
        self.event_manager.trigger_event(event)
        mock_method_1.assert_called_once_with(event)
        mock_method_2.assert_called_once_with(event)
        mock_method_3.assert_called_once_with('dummy_arg', 'dummy_arg2', event)


if __name__ == '__main__':
    unittest.main()

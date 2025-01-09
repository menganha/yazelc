import gc
import unittest
from unittest.mock import Mock

# from event.events import PauseEvent, DeathEvent, CollisionEvent
from event.event_manager import EventManager, Event


class MockPauseEvent(Event):
    pass


class MockDeathEvent(Event):
    pass


class MockCollisionEvent(Event):
    pass


class PauseClass:
    def on_pause(self, event: MockPauseEvent):
        pass


class DeathClass:
    def on_death(self, event: MockDeathEvent):
        pass


class PauseEvent(Event):
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
        self.event_manager.remove_handler(MockDeathEvent, self.instance_with_reference.on_death)
        self.assertTrue(MockDeathEvent not in self.event_manager.subscribers)
        self.assertTrue(MockCollisionEvent in self.event_manager.subscribers)

    def test_remove_all_handlers(self):
        self.event_manager.remove_all_handlers()
        self.assertFalse(self.event_manager.subscribers)

    def test_remove_all_handlers_of_one_event_type(self):
        self.event_manager.remove_all_handlers(MockCollisionEvent)
        self.assertFalse(self.event_manager.subscribers[MockCollisionEvent])
        self.assertTrue(self.event_manager.subscribers[MockDeathEvent])

    def test_weak_ref(self):
        gc.collect()
        self.assertFalse(MockPauseEvent in self.event_manager.subscribers)
        self.assertTrue(MockDeathEvent in self.event_manager.subscribers)

    def test_dispatch_event(self):
        class MockEvent(Event):
            pass

        event = MockEvent()
        mock_method_1 = Mock()
        mock_method_2 = Mock()
        mock_method_3 = Mock()
        self.event_manager.subscribe(MockEvent, mock_method_1)
        self.event_manager.subscribe(MockEvent, mock_method_2)
        self.event_manager.subscribe(MockEvent, mock_method_3)
        self.event_manager.dispatch_event(event)
        mock_method_1.assert_called_once_with(event)
        mock_method_2.assert_called_once_with(event)
        mock_method_3.assert_called_once_with(event)

if __name__ == '__main__':
    unittest.main()

import unittest

import pygame

pygame.init()
pygame.freetype.init()

from yazelc import components as cmp

from yazelc.utils.game_utils import Direction, Status


class TestStateComponents(unittest.TestCase):

    def setUp(self):
        self.state = cmp.State(Status.IDLE, Direction.LEFT)

    def test_state_constructor(self):
        self.assertEqual(self.state.status, Status.IDLE)
        self.assertEqual(self.state.direction, Direction.LEFT)
        self.assertEqual(self.state.prev_status, Status.IDLE)
        self.assertEqual(self.state.prev_direction, Direction.LEFT)

    def test_state_update(self):
        self.state.status = Status.WALKING
        self.state.direction = Direction.RIGHT
        self.assertEqual(self.state.prev_direction, Direction.LEFT)
        self.assertEqual(self.state.prev_status, Status.IDLE)
        self.state.update()
        self.assertEqual(self.state.prev_direction, Direction.RIGHT)
        self.assertEqual(self.state.prev_status, Status.WALKING)

    def test_state_has_changed(self):
        self.state.status = Status.WALKING
        self.state.direction = Direction.RIGHT
        self.assertTrue(self.state.has_changed())


if __name__ == '__main__':
    unittest.main()

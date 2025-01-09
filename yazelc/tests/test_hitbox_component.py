import unittest

import pygame

pygame.init()
pygame.freetype.init()

from yazelc.components import HitBox


class TestHitboxComponent(unittest.TestCase):
    def setUp(self) -> None:
        self.hitbox = HitBox(2, 2, 5, 5, False, 1)

    def test_move(self):
        new_hitbox = self.hitbox.move(2, 2)
        self.assertTrue(isinstance(new_hitbox, HitBox))
        self.assertEqual(new_hitbox.x, 4)
        self.assertEqual(new_hitbox.y, 4)

    def test_skin_depth(self):
        self.assertTrue(self.hitbox.corner_rects[0].topleft == (2, 3))
        self.assertTrue(self.hitbox.corner_rects[0].width == 5)
        self.assertTrue(self.hitbox.corner_rects[0].height == 3)

        self.assertTrue(self.hitbox.corner_rects[1].topleft == (3, 2))
        self.assertTrue(self.hitbox.corner_rects[1].width == 3)
        self.assertTrue(self.hitbox.corner_rects[1].height == 5)


if __name__ == '__main__':
    unittest.main()

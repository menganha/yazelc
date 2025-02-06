import logging

import pygame

from yazelc import components as cmp
from yazelc import zesper
from yazelc.camera import Camera

logger = logging.getLogger(__name__)


class RenderSystem(zesper.Processor):
    def __init__(self, window: pygame.Surface, bgcolor: pygame.Color, world: zesper.World, camera: Camera = None):
        """ Renders to system """
        super().__init__()
        self.window = window
        self.bgcolor = bgcolor
        self.world = world
        self.camera = camera
        self.debug = False

    def process(self):
        self.window.fill(self.bgcolor)

        if self.camera:
            self.camera.update(self.world)

        for ent, (rend, pos) in sorted(self.world.get_components(cmp.Renderable, cmp.Position),
                                       key=lambda x: x[1][0].depth, reverse=False
                                       ):

            if self.camera:
                rel_pos = (round(pos.x - self.camera.position.x), round(pos.y - self.camera.position.y),
                           self.camera.size.x, self.camera.size.y)
            else:
                rel_pos = round(pos.x), round(pos.y)

            # Blending effects
            if blend := self.world.try_component(ent, cmp.BlendEffect):
                new_image = rend.image.copy()
                block = pygame.Surface(rend.image.get_size()).convert_alpha()
                color = pygame.Color('pink') if blend.timer.module(blend.blink_interval) else pygame.Color('lightblue')
                block.fill(color)
                new_image.blit(block, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
                new_image.blit(new_image, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

                blend.timer.tick()
                if blend.timer.has_finished():
                    self.world.remove_component(ent, cmp.BlendEffect)
                img = new_image
            else:
                img = rend.image

            # Render to the window
            self.window.blit(img, rel_pos)

            # On debug mode render all hitboxes
            if self.debug:
                if hitbox := self.world.try_component(ent, cmp.HitBox):
                    hb_surface = pygame.Surface((hitbox.w, hitbox.h), flags=pygame.SRCALPHA)
                    hb_surface.fill(pygame.Color('seashell'))
                    rel_pos_hb = round(hitbox.x - self.camera.position.x), round(hitbox.y - self.camera.position.y)
                    self.window.blit(hb_surface, rel_pos_hb)

        # Render native shapes which are (normally) associated with particle effects
        # TODO: They can be on the the same loop if the position has the absolute flag on
        for ent, (vfx, pos) in self.world.get_components(cmp.Particle, cmp.Position):
            rect = pygame.Rect(round(pos.x), round(pos.y), 1, 1)
            pygame.draw.rect(self.window, vfx.color, rect)

        pygame.display.flip()

import pygame

from yazelc import components as cmp
from yazelc import zesper
from yazelc.camera import Camera
from yazelc.config import Config


class RenderSystem(zesper.Processor):
    def __init__(self, window: pygame.Surface, config: Config, camera: Camera = None):
        # super().__init__()
        self.camera = camera if camera else Camera(0, 0)
        self.window = window
        self.bgcolor = config.window.bgcolor

    def process(self):
        self.window.fill(self.bgcolor)

        # Render sprites
        camera_pos = self.camera.pos
        for ent, (rend, pos) in sorted(self.world.get_components(cmp.Renderable, cmp.Position), key=lambda x: x[1][0].depth, reverse=False):

            if pos.absolute:
                screen_pos = pos
            else:
                screen_pos = pos - camera_pos

            if blend := self.world.try_component(ent, cmp.BlendEffect):
                new_image = rend.image.copy()
                block = pygame.Surface(rend.image.get_size()).convert_alpha()
                if blend.timer.module(blend.blink_interval):
                    color = cfg.C_LIGHT_RED
                else:
                    color = cfg.C_LIGHT_BLUE
                block.fill(color)
                new_image.blit(block, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
                new_image.blit(new_image, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

                blend.timer.tick()
                if blend.timer.has_finished():
                    self.world.remove_component(ent, cmp.BlendEffect)

                img = new_image
            else:
                img = rend.image

            self.window.blit(img, (round(screen_pos.x), round(screen_pos.y)))

        # TODO: They can be on the the same loop if the position has the absolute flag on
        # Render native shapes which are (normally) associated with particle effects
        for ent, (vfx, pos) in self.world.get_components(cmp.Particle, cmp.Position):
            rect = pygame.Rect(round(pos.x - camera_pos.x), round(pos.y - camera_pos.y), 1, 1)
            pygame.draw.rect(self.window, vfx.color, rect)

        # if cfg.DEBUG_MODE:  # On debug mode then render all hitboxes
        #     for ent, (hitbox) in self.world.get_component(cmp.HitBox):
        #         hb_surface = pygame.Surface((hitbox.w, hitbox.h), flags=pygame.SRCALPHA)
        #         hb_surface.fill(cfg.C_TRANSPARENT_BLUE)
        #         self.window.blit(hb_surface, (hitbox.x - round(camera_pos.x), hitbox.y - round(camera_pos.y)))

        pygame.display.flip()

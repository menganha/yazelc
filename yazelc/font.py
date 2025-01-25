import pygame
import pygame.freetype

from yazelc.utils.game_utils import IVec


class Font:
    """
    Utility class to load and render fonts from a simple image or a ttf. The class caches the characters in individual
    pygame surfaces for improved optimization. The image is expected to have the consecutive chars in the same order as
    the ascii table.
    """

    def __init__(self, char_surfaces: dict[str, tuple[pygame.Surface, int]], height: int, color: pygame.Color):
        self.height = height
        self._char_surfaces = char_surfaces
        self.color = color  # we have it for reference

    def render_to(self, target_surface: pygame.Surface, target_coord: IVec, text: str,
                  extra_line_spacing: int = 0):
        """ Returns a surface containing all the text. It supports multiline text """
        x_offset = target_coord.x
        y_offset = target_coord.y
        for line in text.splitlines():
            for char in line:
                char_sur, width = self._char_surfaces[char]
                target_surface.blit(char_sur, (x_offset, y_offset))
                x_offset += width
            x_offset = target_coord.x
            y_offset += self.height + extra_line_spacing

    def render(self, text: str, extra_line_spacing: int = 0) -> pygame.Surface:
        """ Renders to a transparent surface where the input texts fits exactly """
        lines = text.splitlines()
        sur_width = self._get_max_width(lines)
        sur_height = self.height * len(lines) + extra_line_spacing * (len(lines) - 1)
        surface = pygame.Surface((sur_width, sur_height), flags=pygame.SRCALPHA)
        self.render_to(surface, IVec(0, 0), text, extra_line_spacing)
        return surface

    def get_width(self, text: str) -> int:
        """ Checks if line of text fits on box. Does not support multiline """
        total_width = sum(self._char_surfaces[char][1] for char in text)
        return total_width

    def _get_max_width(self, lines: list[str]) -> int:
        """ Returns the max width of a list of lines """
        max_width = 0
        for line in lines:
            line_width = self.get_width(line)
            max_width = max(max_width, line_width)
        return max_width

    @classmethod
    def from_surface(cls, surface: pygame.Surface, color: pygame.Color):
        """ Admits surfaces with the printable ascii characters organizes in the usual 16x6 table """
        w, h = surface.get_size()
        width, height = IVec(w // 16, h // 6)

        char_surfaces = dict()
        pos = [0, 0]
        green_color = pygame.Color(0, 255, 0)
        for idx in range(ord(' '), ord('~') + 1):
            char = chr(idx)
            actual_width = 0
            for x in range(pos[0], pos[0] + width):
                color_at_x = surface.get_at((x, pos[1]))
                if color_at_x == green_color:
                    break
                else:
                    actual_width += 1

            sur = surface.subsurface(pygame.Rect(pos[0], pos[1], actual_width, height))
            char_surfaces[char] = (sur, actual_width)
            if (idx + 1) % 16:
                pos[0] += width
            else:
                pos[0] = 0
                pos[1] += height

        instance = cls(char_surfaces, height, color)
        return instance

    @classmethod
    def from_font(cls, font: pygame.font.Font, color: pygame.Color):

        height = font.get_linesize()

        char_surfaces = dict()
        for idx in range(ord(' '), ord('~') + 1):
            char = chr(idx)
            surface = font.render(char, True, color)
            surface = surface.convert_alpha()
            char_surfaces[char] = (surface, surface.get_width())

        instance = cls(char_surfaces, height, color)
        return instance

    def save_to_image_atlas(self, output_path: str):
        surface_atlas = pygame.Surface((8 * 16, self.height * 6))
        x = 0
        y = 0
        for idx in range(ord(' '), ord('~') + 1):
            char = chr(idx)
            char_surface, width = self._char_surfaces[char]
            surface_atlas.blit(char_surface, (x, y))
            if (idx + 1) % 16:
                x += width
            else:
                x = 0
                y += self.height

        pygame.image.save(surface_atlas, output_path)

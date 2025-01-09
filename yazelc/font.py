import pygame
import pygame.freetype


class Font:
    """ Wrapper around the pygame's freetype Fonts """

    def __init__(self, font: pygame.freetype.Font, size: int, fgcolor: pygame.Color):
        self.font = font
        self.size = size
        self.fgcolor = fgcolor
        self.line_spacing = self.font.get_sized_height(size)
        self.advance = self.font.get_rect(' ', size=size).width

    def render_text_at(self, text: str, target_surface: pygame.Surface,
                       pos_x: int | None = None, pos_y: int | None = None) -> pygame.Rect:
        """
        Renders text at a specific location of the target surface. If a dimension is not explicitly provided, the
        function will try to center the text on that dimension. Keyword arguments are passed directly to the
        base functions
        """
        width, height = target_surface.get_size()

        rect = self.font.get_rect(text, size=self.size)
        center_x = (-rect.width + width) // 2
        center_y = (-rect.height + height) // 2

        target_pos_x = center_x if pos_x is None else pos_x
        target_pos_y = center_y if pos_y is None else pos_y
        return self.font.render_to(target_surface, (target_pos_x, target_pos_y), text, size=self.size,
                                   fgcolor=self.fgcolor
                                   )

    def render(self, text: str, center: bool = False) -> pygame.Surface:

        max_width, max_height, current_height = 0, 0, self.line_spacing
        text_lines = text.splitlines()
        if len(text_lines) > 1:
            for line in text_lines:
                _, _, width, height = self.font.get_rect(line, size=self.size)
                height += current_height
                max_width = max(max_width, width)
                max_height = max(max_height, height)
                current_height += self.line_spacing
            surface = pygame.Surface((max_width, max_height))

            current_height = self.line_spacing
            for line in text_lines:
                if center:
                    x = (max_width - self.font.get_rect(line, size=self.size).width) // 2
                else:
                    x = 0
                self.font.render_to(surface, (x, current_height), line, size=self.size, fgcolor=self.fgcolor)
                current_height += self.line_spacing
        else:
            surface, _ = self.font.render(text, size=self.size, fgcolor=self.fgcolor)

        return surface

    def fits_on_box(self, text: str, box_width: int):
        """ Checks if the sentence with the next word added in fits in the give width """
        bounds = self.font.get_rect(text, size=self.size)
        return bounds.width < box_width

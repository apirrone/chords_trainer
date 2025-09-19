import pygame

# TODO two color themes for view mode and train mode

BG_COLOR = (61, 59, 161)
TEXT_COLOR = (255, 255, 255)


def in_rect(rect, pos):
    x, y, w, h = rect
    return x <= pos[0] <= x + w and y <= pos[1] <= y + h


class Button:
    def __init__(self, pos, size, text, font_size=20):
        self.pos = pos
        self.size = size
        self.text = text
        self.font_size = font_size
        self.bg_color = BG_COLOR

    def draw(self, screen):
        pygame.draw.rect(
            screen,
            self.bg_color,
            (*self.pos, *self.size),
            0,
        )
        pygame.draw.rect(
            screen,
            TEXT_COLOR,
            (*self.pos, *self.size),
            1,
        )

        font = pygame.font.SysFont("Arial", self.font_size)
        text = font.render(self.text, True, TEXT_COLOR)
        screen.blit(
            text,
            (
                self.pos[0] + (self.size[0] - text.get_width()) / 2,
                self.pos[1] + (self.size[1] - text.get_height()) / 2,
            ),
        )

    def hover(self, mouse_pos):
        return in_rect(
            (self.pos[0], self.pos[1], self.size[0], self.size[1]), mouse_pos
        )

    def update(self, events):
        for event in events:
            if self.hover(pygame.mouse.get_pos()):
                self.bg_color = (41, 39, 141)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    return True
            else:
                self.bg_color = BG_COLOR
        return False

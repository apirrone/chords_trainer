import pygame
from chords_trainer.chords import is_same_chord
from chords_trainer.utils import TEXT_COLOR


class Views:
    def __init__(self, screen, window_size):
        self.screen = screen
        self.window_size = window_size
        self.current_view = self.display_chord_view  # default view

    def get_current_view(self):
        return self.current_view.__name__

    def switch(self):
        if self.current_view == self.display_chord_view:
            self.current_view = self.train_view
        else:
            self.current_view = self.display_chord_view

    def switch_to_train_view(self):
        self.current_view = self.train_view

    def switch_to_display_chord_view(self):
        self.current_view = self.display_chord_view

    def view(self, data, i=0, current_train_chord=None):
        return self.current_view(data, i, current_train_chord)

    def display_chord_view(self, data, i=0, current_train_chord=None):
        if len(data["names"]) == 0:
            return

        if len(data["names"]) > 1:
            # write "press space to view alternate chord" in the top right
            font = pygame.font.SysFont("Arial", 20)
            text = font.render("tap to view alternate chord", True, TEXT_COLOR)
            self.screen.blit(text, (self.window_size[0] - text.get_width() - 10, 0))

        # display main chord name in big in the middle
        font = pygame.font.SysFont("Arial", 60)
        text = font.render(data["names"][i], True, TEXT_COLOR)
        self.screen.blit(
            text,
            (
                self.window_size[0] // 2 - text.get_width() // 2,
                self.window_size[1] // 2 - text.get_height() // 2,
            ),
        )

        # display abbrs smaller below
        font = pygame.font.SysFont("Arial", 30)
        text = font.render(", ".join(data["abbrs"][i]), True, TEXT_COLOR)
        self.screen.blit(
            text,
            (
                self.window_size[0] // 2 - text.get_width() // 2,
                self.window_size[1] // 2 + 30 + text.get_height() // 2,
            ),
        )

        # Display degrees under the chord_notes in small
        font = pygame.font.SysFont("Arial", 20)
        for j, chord_note in enumerate(data["chord_notes"]):
            text = font.render(data["degrees"][i][chord_note], True, TEXT_COLOR)
            self.screen.blit(text, (3 + j * 30, 30))

    def train_view(self, data, i=0, current_train_chord=None):
        color = (255, 255, 0)
        same_chord = False

        if len(data["names"]) != 0:
            same_chord = is_same_chord(data["names"][0], current_train_chord[0])
            color = (0, 255, 0) if same_chord else (255, 0, 0)

        # display main chord name in big in the middle
        font = pygame.font.SysFont("Arial", 60)
        text = font.render(current_train_chord[0], True, color)
        self.screen.blit(
            text,
            (
                self.window_size[0] // 2 - text.get_width() // 2,
                self.window_size[1] // 2 - text.get_height() // 2,
            ),
        )

        # # display abbrs smaller below
        # font = pygame.font.SysFont("Arial", 30)
        # text = font.render(", ".join(data["abbrs"][i]), True, TEXT_COLOR)
        # screen.blit(
        #     text,
        #     (
        #         window_size[0] // 2 - text.get_width() // 2,
        #         window_size[1] // 2 + 30 + text.get_height() // 2,
        #     ),
        # )

        # DEBUG
        # display main chord name in big in the middle

        if len(data["names"]) == 0:
            return
        font = pygame.font.SysFont("Arial", 30)
        text = font.render(data["names"][0], True, TEXT_COLOR)
        self.screen.blit(
            text,
            (
                self.window_size[0] // 3 - text.get_width() // 3,
                self.window_size[1] // 3 - text.get_height() // 3,
            ),
        )

        return same_chord

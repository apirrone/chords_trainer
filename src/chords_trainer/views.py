import pygame
from chords_trainer.chords import is_same_chord, gen_random_chord
from chords_trainer.utils import TEXT_COLOR, Button


class View:
    def __init__(self, screen, window_size):
        self.screen = screen
        self.window_size = window_size

    def render(self, data, i=0, current_train_chord=None):
        # Always display the currently played notes at the top left
        font = pygame.font.SysFont("Arial", 30)
        text = font.render(" ".join(data["chord_notes"]), True, TEXT_COLOR)
        self.screen.blit(text, (0, 0))


class Views:
    def __init__(self, screen, window_size, train_mode=False):
        self.screen = screen
        self.window_size = window_size
        self.display_chord_view = DisplayChordView(screen, window_size)
        self.train_view = TrainView(screen, window_size)

        self.train_mode_button = Button(
            (window_size[0] - 100, window_size[1] - 30), (100, 30), "Train mode"
        )

        if train_mode:
            self.current_view = self.train_view
        else:
            self.current_view = self.display_chord_view  # default view

    def handle_events(
        self, events, data, alternate_chord, current_train_chord, difficulty
    ):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    alternate_chord = (
                        (alternate_chord + 1) % len(data["names"])
                        if len(data["names"]) > 1
                        else 0
                    )

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if not self.train_mode_button.hover(event.pos):
                        alternate_chord = (
                            (alternate_chord + 1) % len(data["names"])
                            if len(data["names"]) > 1
                            else 0
                        )

        ret = self.train_mode_button.update(events)

        if ret:
            current_train_chord = gen_random_chord(difficulty=difficulty)
            self.switch()

    def switch(self):
        if self.current_view == self.display_chord_view:
            self.current_view = self.train_view
        else:
            self.current_view = self.display_chord_view

    def render(self, data, i=0, current_train_chord=None):
        self.train_mode_button.render(self.screen)
        return self.current_view.render(data, i, current_train_chord)

    def get_current_view(self):
        if self.current_view == self.display_chord_view:
            return "display_chord_view"
        else:
            return "train_view"


class DisplayChordView(View):
    def __init__(self, screen, window_size):
        super().__init__(screen, window_size)
        pass

    def render(self, data, i=0, current_train_chord=None):
        super().render(data, i, current_train_chord)
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

        return False


class TrainView(View):
    def __init__(self, screen, window_size):
        super().__init__(screen, window_size)
        pass

    def render(self, data, i=0, current_train_chord=None):
        super().render(data, i, current_train_chord)
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

        font = pygame.font.SysFont("Arial", 20)
        text = font.render("TRAIN MODE", True, (255, 255, 0))
        self.screen.blit(text, (0, self.window_size[1] - text.get_height()))

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

        # if same_chord:
        #     print("AAAAAAAAAAAAAA")

        return same_chord

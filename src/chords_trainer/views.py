import time

import pygame

from chords_trainer.chords import difficulties, gen_random_chord, is_same_chord
from chords_trainer.stats import Stats
from chords_trainer.utils import TEXT_COLOR, Button


class View:
    def __init__(self, screen, window_size, difficulty):
        self.screen = screen
        self.window_size = window_size
        self.difficulty = difficulty

    def render(self, data, alternate_chord_idx=0):
        # Always display the currently played notes at the top left
        font = pygame.font.SysFont("Arial", 30)
        text = font.render(" ".join(data["chord_notes"]), True, TEXT_COLOR)
        self.screen.blit(text, (0, 0))


class Views:
    def __init__(self, screen, window_size, interfaces, difficulty, train_mode=False):
        self.screen = screen
        self.window_size = window_size
        self.display_chord_view = DisplayChordView(screen, window_size, difficulty)
        self.train_view = TrainView(screen, window_size, difficulty)
        self.interfaces = interfaces
        self.chosen_interface_idx = 1
        self.change_interface = False
        self.difficulty = difficulty
        self.alternate_chord_idx = 0
        self.current_train_chord = gen_random_chord(difficulty=difficulty)

        self.train_mode_button = Button(
            (window_size[0] - 100, window_size[1] - 30), (100, 30), "Train mode"
        )

        self.interfaces_button = Button(
            (self.window_size[0] - 200, 0),
            (200, 30),
            f"{self.interfaces[self.chosen_interface_idx]}",
            fit_box_to_text_width=True,
        )

        if train_mode:
            self.current_view = self.train_view
        else:
            self.current_view = self.display_chord_view  # default view

    def get_chosen_interface(self):
        return self.interfaces[self.chosen_interface_idx]

    def interface_has_changed(self):
        ret = False
        if self.change_interface:
            ret = True
            self.change_interface = False
        return ret

    def handle_events(self, events, data):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.alternate_chord_idx = (
                        (self.alternate_chord_idx + 1) % len(data["names"])
                        if len(data["names"]) > 1
                        else 0
                    )

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if not self.train_mode_button.hover(event.pos):
                        self.alternate_chord_idx = (
                            (self.alternate_chord_idx + 1) % len(data["names"])
                            if len(data["names"]) > 1
                            else 0
                        )

        toggle_train_mode = self.train_mode_button.update(events)

        if toggle_train_mode:
            self.switch()

        toggle_interface = self.interfaces_button.update(events)
        if toggle_interface:
            self.chosen_interface_idx = (
                (self.chosen_interface_idx + 1) % len(self.interfaces)
                if len(self.interfaces) > 1
                else 0
            )
            self.interfaces_button = Button(
                (self.window_size[0] - 200, 0),
                (200, 30),
                f"{self.interfaces[self.chosen_interface_idx]}",
                fit_box_to_text_width=True,
            )
            self.change_interface = True

        if self.current_view == self.train_view:  # A little lame
            toggle_difficulty = self.current_view.difficulty_button.update(events)
            if toggle_difficulty:
                nb_difficulties = len(difficulties)
                self.difficulty = (self.difficulty + 1) % nb_difficulties
                self.current_view.difficulty_button = Button(
                    (0, self.window_size[1] - 30),
                    (200, 30),
                    f"Difficulty: {self.difficulty}",
                    fit_box_to_text_width=True,
                )

    def switch(self):
        if self.current_view == self.display_chord_view:
            self.current_view = self.train_view
        else:
            self.current_view = self.display_chord_view

    def render(self, data):
        self.train_mode_button.render(self.screen)
        self.interfaces_button.render(self.screen)
        next_train_chord = self.current_view.render(
            data, self.alternate_chord_idx, self.current_train_chord
        )

        if next_train_chord:
            self.current_train_chord = gen_random_chord(difficulty=self.difficulty)
            self.current_view.next_train_chord = False

    def get_current_view(self):
        if self.current_view == self.display_chord_view:
            return "display_chord_view"
        else:
            return "train_view"


class DisplayChordView(View):
    def __init__(self, screen, window_size, difficulty):
        super().__init__(screen, window_size, difficulty)
        pass

    def render(self, data, alternate_chord_idx=0, current_train_chord=None):
        super().render(data, alternate_chord_idx)
        if len(data["names"]) == 0:
            return

        if len(data["names"]) > 1:
            # write "press space to view alternate chord" in the top right
            font = pygame.font.SysFont("Arial", 20)
            text = font.render("tap to view alternate chord", True, TEXT_COLOR)
            self.screen.blit(text, (self.window_size[0] - text.get_width() - 10, 50))

        # display main chord name in big in the middle
        font = pygame.font.SysFont("Arial", 60)
        text = font.render(data["names"][alternate_chord_idx], True, TEXT_COLOR)
        self.screen.blit(
            text,
            (
                self.window_size[0] // 2 - text.get_width() // 2,
                self.window_size[1] // 2 - text.get_height() // 2,
            ),
        )

        # display abbrs smaller below
        font = pygame.font.SysFont("Arial", 30)
        text = font.render(
            ", ".join(data["abbrs"][alternate_chord_idx]), True, TEXT_COLOR
        )
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
            text = font.render(
                data["degrees"][alternate_chord_idx][chord_note], True, TEXT_COLOR
            )
            self.screen.blit(text, (3 + j * 30, 30))

        return False


class TrainView(View):
    def __init__(self, screen, window_size, difficulty):
        super().__init__(screen, window_size, difficulty)
        # left bottom corner
        self.difficulty_button = Button(
            (0, window_size[1] - 30),
            (200, 30),
            f"Difficulty: {self.difficulty}",
            fit_box_to_text_width=True,
        )
        self.next_train_chord = False
        self.stats = Stats()
        self.current_chord_start_time = time.time()
        self.current_chord_mistakes = 0  # reserved for future detailed counts
        self.registered_mistake = False  # debounce mistake per attempt
        self.attempt_has_mistake = False

    def render(self, data, alternate_chord_idx=0, current_train_chord=None):
        super().render(data, alternate_chord_idx)
        color = (255, 255, 0)
        same_chord = False

        if len(data["names"]) == 0:  # released
            self.registered_mistake = False
        else:
            same_chord = is_same_chord(data["names"][0], current_train_chord[0])
            color = (0, 255, 0) if same_chord else (255, 0, 0)
            # # display abbrs smaller below
            font = pygame.font.SysFont("Arial", 30)
            text = font.render(
                ", ".join(data["abbrs"][alternate_chord_idx]), True, TEXT_COLOR
            )
            self.screen.blit(
                text,
                (
                    self.window_size[0] // 2 - text.get_width() // 2,
                    self.window_size[1] // 2 + 30 + text.get_height() // 2,
                ),
            )

            # Track if a mistake occurred during this attempt (debounced).
            if not same_chord and not self.registered_mistake:
                self.attempt_has_mistake = True
                self.registered_mistake = True

        if same_chord:
            self.next_train_chord = True

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

        self.difficulty_button.render(self.screen)

        if len(data["names"]) != 0:
            font = pygame.font.SysFont("Arial", 30)
            text = font.render(data["names"][0], True, TEXT_COLOR)
            self.screen.blit(
                text,
                (
                    self.window_size[0] // 3 - text.get_width() // 3,
                    self.window_size[1] // 3 - text.get_height() // 3,
                ),
            )

        if self.next_train_chord and len(data["names"]) == 0:
            # Register the correct solve now that the chord has been released
            time_taken = time.time() - self.current_chord_start_time
            self.stats.record(
                current_train_chord[0],
                self.difficulty,
                time_taken,
                correct=True,
                mistakes=1 if self.attempt_has_mistake else 0,
            )
            print("correct")
            print(self.stats)
            self.current_chord_start_time = time.time()
            self.current_chord_mistakes = 0
            self.attempt_has_mistake = False
            return True

        return False

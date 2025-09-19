import argparse
import mido

import pygame

from chords_trainer.utils import BG_COLOR, TEXT_COLOR, Button
from chords_trainer.chords import gen_random_chord
from chords_trainer.synth import SineMIDISynth
from chords_trainer.midi import MidiProcessor
from chords_trainer.views import Views

pygame.display.init()
pygame.font.init()

WINDOW_SIZE = (600, 300)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--difficulty",
        type=int,
        default=0,
        help="Training difficulty (0=easy, 1=medium, 2=hard)",
    )
    parser.add_argument("--synth", action="store_true", help="Enable MIDI synth")
    args = parser.parse_args()

    screen = pygame.display.set_mode(
        WINDOW_SIZE, flags=pygame.SRCALPHA + pygame.NOFRAME
    )
    interfaces = mido.get_input_names()
    print("Detected interfaces : ")
    for i, interface in enumerate(interfaces):
        print(f"{i} : {interface}")
    midi_processor = MidiProcessor(interfaces[1])

    if args.synth:
        SineMIDISynth().start()

    views = Views(screen, WINDOW_SIZE)

    data = {"chord_notes": [], "names": [], "abbrs": [], "degrees": []}

    train_mode_button = Button(
        (WINDOW_SIZE[0] - 100, WINDOW_SIZE[1] - 30), (100, 30), "Train mode"
    )

    alternate_chord = 0
    current_train_chord = gen_random_chord(
        difficulty=args.difficulty
    )  # tuple like ('FAdd9', 'F', [0, 4, 7]), abbr, root, pattern
    next_train_chord = False

    while True:
        screen.fill(BG_COLOR)

        if not midi_processor.data_queue.empty():
            data = midi_processor.data_queue.get(False)
            alternate_chord = 0
            if len(data["names"]) == 0 and next_train_chord:
                current_train_chord = gen_random_chord(difficulty=args.difficulty)
                next_train_chord = False

        font = pygame.font.SysFont("Arial", 30)
        text = font.render(" ".join(data["chord_notes"]), True, TEXT_COLOR)
        screen.blit(text, (0, 0))

        success = views.view(
            data, i=alternate_chord, current_train_chord=current_train_chord
        )
        if success:
            next_train_chord = True

        # Press space to view alternate chord
        events = pygame.event.get()
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
                    if not train_mode_button.hover(event.pos):
                        alternate_chord = (
                            (alternate_chord + 1) % len(data["names"])
                            if len(data["names"]) > 1
                            else 0
                        )

        ret = train_mode_button.update(events)

        if ret:
            views.switch()
            current_train_chord = gen_random_chord(difficulty=args.difficulty)

        train_mode_button.draw(screen)

        if views.get_current_view() == "train_view":
            font = pygame.font.SysFont("Arial", 20)
            text = font.render("TRAIN MODE", True, (255, 255, 0))
            screen.blit(text, (0, WINDOW_SIZE[1] - text.get_height()))

        pygame.display.flip()

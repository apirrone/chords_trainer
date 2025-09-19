import argparse
import mido

import pygame

from chords_trainer.utils import BG_COLOR
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
    parser.add_argument("--train", action="store_true", help="Enable training mode")
    parser.add_argument("--synth", action="store_true", help="Enable MIDI synth")
    args = parser.parse_args()

    screen = pygame.display.set_mode(
        WINDOW_SIZE, flags=pygame.SRCALPHA + pygame.NOFRAME
    )

    interfaces = mido.get_input_names()
    views = Views(
        screen,
        WINDOW_SIZE,
        interfaces,
        difficulty=args.difficulty,
        train_mode=args.train,
    )

    midi_processor = MidiProcessor(views.get_chosen_interface())

    if args.synth:
        synth = SineMIDISynth(views.get_chosen_interface())

    data = {"chord_notes": [], "names": [], "abbrs": [], "degrees": []}

    while True:
        screen.fill(BG_COLOR)

        if not midi_processor.data_queue.empty():
            data = midi_processor.data_queue.get(False)

        views.render(data)

        if views.interface_has_changed():
            midi_processor.stop()

            midi_processor = MidiProcessor(views.get_chosen_interface())
            if args.synth:
                synth.stop()
                synth = SineMIDISynth(views.get_chosen_interface())

        events = pygame.event.get()
        views.handle_events(events, data)

        pygame.display.flip()

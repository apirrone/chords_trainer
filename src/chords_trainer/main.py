import multiprocessing
from threading import Thread
from multiprocessing import Queue
import argparse

import pygame

from chords_trainer.utils import BG_COLOR, TEXT_COLOR, Button
from chords_trainer.chords import find_chords, gen_random_chord, is_same_chord
from chords_trainer.synth import SineMIDISynth

pygame.display.init()
pygame.font.init()


data_queue = Queue()


def midi_thread():
    import mido

    # TODO handle flat notes
    notes = ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]
    min_note = 21

    pressed = {}
    interfaces = mido.get_input_names()
    print("Detected interfaces : ")
    for i, interface in enumerate(interfaces):
        print(f"{i} : {interface}")
    # inport = mido.open_input("uMIDI/O22:uMIDI/O22 MIDI 1 20:0")
    inport = mido.open_input(
        interfaces[1]
    )  # TODO button to iterate over detected interfaces
    for msg in inport:
        if "note" not in msg.type:
            continue
        note = int(msg.note)

        if msg.type == "note_on":
            if note not in pressed:
                pressed[note] = 1
        elif msg.type == "note_off":
            if note in pressed:
                del pressed[note]

        chord = tuple([(note - min_note) % 12 for note in sorted(pressed.keys())])
        chord_notes = [notes[note] for note in chord]
        names, abbrs, degrees = find_chords(" ".join([notes[note] for note in chord]))

        data_queue.put(
            {
                "chord_notes": chord_notes,
                "names": names,
                "abbrs": abbrs,
                "degrees": degrees,
            }
        )


def display_chord(data, i=0):
    if len(data["names"]) == 0:
        return

    if len(data["names"]) > 1:
        # write "press space to view alternate chord" in the top right
        font = pygame.font.SysFont("Arial", 20)
        text = font.render("tap to view alternate chord", True, TEXT_COLOR)
        screen.blit(text, (window_size[0] - text.get_width() - 10, 0))

    # display main chord name in big in the middle
    font = pygame.font.SysFont("Arial", 60)
    text = font.render(data["names"][i], True, TEXT_COLOR)
    screen.blit(
        text,
        (
            window_size[0] // 2 - text.get_width() // 2,
            window_size[1] // 2 - text.get_height() // 2,
        ),
    )

    # display abbrs smaller below
    font = pygame.font.SysFont("Arial", 30)
    text = font.render(", ".join(data["abbrs"][i]), True, TEXT_COLOR)
    screen.blit(
        text,
        (
            window_size[0] // 2 - text.get_width() // 2,
            window_size[1] // 2 + 30 + text.get_height() // 2,
        ),
    )

    # Display degrees under the chord_notes in small
    font = pygame.font.SysFont("Arial", 20)
    for j, chord_note in enumerate(data["chord_notes"]):
        text = font.render(data["degrees"][i][chord_note], True, TEXT_COLOR)
        screen.blit(text, (3 + j * 30, 30))


def train_mode(data, current_train_chord):
    color = (255, 255, 0)
    same_chord = False

    if len(data["names"]) != 0:
        same_chord = is_same_chord(data["names"][0], current_train_chord[0])
        color = (0, 255, 0) if same_chord else (255, 0, 0)

    # display main chord name in big in the middle
    font = pygame.font.SysFont("Arial", 60)
    text = font.render(current_train_chord[0], True, color)
    screen.blit(
        text,
        (
            window_size[0] // 2 - text.get_width() // 2,
            window_size[1] // 2 - text.get_height() // 2,
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
    screen.blit(
        text,
        (
            window_size[0] // 3 - text.get_width() // 3,
            window_size[1] // 3 - text.get_height() // 3,
        ),
    )

    return same_chord


window_size = (600, 300)
screen = pygame.display.set_mode(window_size, flags=pygame.SRCALPHA + pygame.NOFRAME)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--difficulty", type=int, default=0, help="Training difficulty (0=easy, 1=medium, 2=hard)")
    args = parser.parse_args()
    
    VIEW_MODE = True

    Thread(target=midi_thread).start()  # Was using multiprocessing.Process before
    synth = SineMIDISynth()
    synth.start()

    data = {"chord_notes": [], "names": [], "abbrs": [], "degrees": []}

    train_mode_button = Button(
        (window_size[0] - 100, window_size[1] - 30), (100, 30), "Train mode"
    )

    alternate_chord = 0
    current_train_chord = gen_random_chord(
        difficulty=args.difficulty
    )  # tuple like ('FAdd9', 'F', [0, 4, 7]), abbr, root, pattern
    next_train_chord = False

    while True:
        screen.fill(BG_COLOR)

        try:
            data = data_queue.get(False)
            alternate_chord = 0
            if len(data["names"]) == 0 and next_train_chord:
                current_train_chord = gen_random_chord(difficulty=args.difficulty)
                next_train_chord = False
        except multiprocessing.queues.Empty:
            pass

        font = pygame.font.SysFont("Arial", 30)
        text = font.render(" ".join(data["chord_notes"]), True, TEXT_COLOR)
        screen.blit(text, (0, 0))

        if VIEW_MODE:
            display_chord(data, i=alternate_chord)
        else:
            success = train_mode(data, current_train_chord)
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
            VIEW_MODE = not VIEW_MODE
            current_train_chord = gen_random_chord(difficulty=args.difficulty)

        train_mode_button.draw(screen)

        if not VIEW_MODE:
            font = pygame.font.SysFont("Arial", 20)
            text = font.render("TRAIN MODE", True, (255, 255, 0))
            screen.blit(text, (0, window_size[1] - text.get_height()))

        pygame.display.flip()

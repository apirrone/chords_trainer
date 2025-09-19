import mido
from threading import Thread
from queue import Queue
from chords_trainer.chords import find_chords
from chords_trainer.chords import chr_scale as notes


class MidiProcessor:
    def __init__(self, interface):
        self.interface = interface
        self.data_queue = Queue()
        self.min_note = 21
        self.thread = Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):  # TODO handle flat notes
        pressed = {}
        inport = mido.open_input(self.interface)
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

            chord = tuple(
                [(note - self.min_note) % 12 for note in sorted(pressed.keys())]
            )
            chord_notes = [notes[note] for note in chord]
            names, abbrs, degrees = find_chords(
                " ".join([notes[note] for note in chord])
            )

            self.data_queue.put(
                {
                    "chord_notes": chord_notes,
                    "names": names,
                    "abbrs": abbrs,
                    "degrees": degrees,
                }
            )

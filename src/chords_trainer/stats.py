from dataclasses import dataclass


@dataclass
class ChordStats:
    name: str
    difficulty: int
    occurrences: int = 0
    mistakes: int = 0
    avg_time: float = 0.0


class Stats:
    def __init__(self):
        self.chords = {}

    def record(self, chord_name, difficulty, time_taken, correct):
        if chord_name not in self.chords:
            self.chords[chord_name] = ChordStats(name=chord_name, difficulty=difficulty)

        chord_stats = self.chords[chord_name]
        chord_stats.occurrences += 1
        if not correct:
            chord_stats.mistakes += 1

        # Update average time using incremental formula
        if correct:
            n = chord_stats.occurrences
            chord_stats.avg_time += (time_taken - chord_stats.avg_time) / n

    def __repr__(self):
        ret = "Stats:\n"
        for chord in self.chords.values():
            ret += f"{chord.name} (Diff {chord.difficulty}): Occurrences={chord.occurrences}, Mistakes={chord.mistakes}, Avg Time={chord.avg_time:.2f}s\n"

        return ret

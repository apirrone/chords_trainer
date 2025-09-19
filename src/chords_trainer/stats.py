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

    def record(self, chord_name, difficulty, time_taken, correct, mistakes=0):
        """Record one training attempt for a chord.

        occurrences counts attempts. mistakes increments by the number of
        mistakes made during the attempt (commonly 0 or 1). avg_time only
        updates for successful attempts.
        """
        if chord_name not in self.chords:
            self.chords[chord_name] = ChordStats(name=chord_name, difficulty=difficulty)

        chord_stats = self.chords[chord_name]
        chord_stats.occurrences += 1
        chord_stats.mistakes += int(mistakes)

        # Update average time using incremental formula (on correct only)
        if correct:
            n = chord_stats.occurrences
            chord_stats.avg_time += (time_taken - chord_stats.avg_time) / n

    def __repr__(self):
        ret = "Stats:\n"
        for chord in self.chords.values():
            ret += f"{chord.name} (Diff {chord.difficulty}): Occurrences={chord.occurrences}, Mistakes={chord.mistakes}, Avg Time={chord.avg_time:.2f}s\n"

        return ret

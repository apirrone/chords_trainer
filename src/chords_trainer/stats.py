import time
from dataclasses import dataclass
import json
import os


@dataclass
class ChordStats:
    name: str
    difficulty: int
    occurrences: int = 0
    mistakes: int = 0
    successes: int = 0
    avg_time: float = 0.0
    # SM-2 scheduling fields
    ef: float = 2.5           # easiness factor
    reps: int = 0             # successful repetition count
    interval: float = 0.0     # interval in days
    due_ts: float = 0.0       # next due timestamp (epoch seconds)
    last_quality: int = 0
    created_ts: float = 0.0
    updated_ts: float = 0.0


class Stats:
    def __init__(self):
        if os.path.exists("stats.json"):
            self.chords = json.load(open("stats.json", "r"))
            # Convert dicts to ChordStats
            for k, v in self.chords.items():
                self.chords[k] = ChordStats(**v)
        else:
            self.chords = {}

    def record(self, chord_name, difficulty, time_taken, correct, mistakes=0):
        """Record one training attempt and update SM-2 scheduling.

        occurrences counts attempts. mistakes increments by the number of
        mistakes made during the attempt (commonly 0 or 1). avg_time only
        updates for successful attempts. SM-2 is updated using a derived
        quality score (0-5).
        """
        now = time.time()
        if chord_name not in self.chords:
            self.chords[chord_name] = ChordStats(
                name=chord_name, difficulty=difficulty, created_ts=now
            )

        chord_stats = self.chords[chord_name]
        chord_stats.occurrences += 1
        chord_stats.mistakes += int(mistakes)
        chord_stats.updated_ts = now

        # Update average time using incremental formula (on correct only)
        if correct:
            n = chord_stats.occurrences
            chord_stats.avg_time += (time_taken - chord_stats.avg_time) / n
            chord_stats.successes += 1

        # Derive a quality score for SM-2 and update spacing
        q = self._derive_quality(time_taken=time_taken, correct=correct, mistakes=mistakes)
        self._update_sm2(chord_stats, q)
        # Persist after each record so scheduling/state survives across days
        self.save()

    # ---------- SM-2 helpers ----------
    @staticmethod
    def _derive_quality(*, time_taken: float, correct: bool, mistakes: int) -> int:
        """Map performance to an SM-2 quality 0..5.

        Heuristic:
        - Perfect, fast (<2s): 5
        - Perfect: 4
        - One mistake: 3
        - Multiple mistakes or very slow (>10s): 2
        - If not correct: 1 (seen, failed)
        """
        if not correct:
            return 1
        if mistakes <= 0 and time_taken <= 2.0:
            return 5
        if mistakes <= 0:
            return 4
        # Any mistake counts as a failed recall for SRS purposes
        if mistakes >= 1:
            return 2
        return 3

    @staticmethod
    def _update_sm2(cs: ChordStats, quality: int) -> None:
        # SM-2 easiness update
        ef = cs.ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        cs.ef = max(1.3, ef)
        now = time.time()
        if quality >= 3:
            # success
            if cs.reps == 0:
                cs.interval = 1.0
            elif cs.reps == 1:
                cs.interval = 6.0
            else:
                cs.interval = cs.interval * cs.ef
            cs.reps += 1
            cs.due_ts = now + cs.interval * 86400.0
        else:
            # failure: reset
            cs.reps = 0
            cs.interval = 1.0
            # reattempt soon within the same session
            cs.due_ts = now + 30.0
        cs.last_quality = int(quality)

    # Utility to get due timestamp for a chord (defaults new chords to now)
    def get_due(self, chord_name: str) -> float:
        cs = self.chords.get(chord_name)
        if cs is None:
            return 0.0
        return float(cs.due_ts)

    def save(self):
        json.dump(
            self.chords, open("stats.json", "w"), indent=4, default=lambda o: o.__dict__
        )

    def __repr__(self):
        ret = "Stats:\n"
        for chord in self.chords.values():
            ret += f"{chord.name} (Diff {chord.difficulty}): Occurrences={chord.occurrences}, Mistakes={chord.mistakes}, Avg Time={chord.avg_time:.2f}s\n"

        return ret

# sine_midi_synth_debug.py
import threading, math, time
import numpy as np
import sounddevice as sd
import mido


class SineMIDISynth:
    def __init__(
        self,
        interface,
        *,
        samplerate=48000,
        blocksize=256,
        master_gain=0.2,
        attack_ms=5,
        release_ms=30,
        backend=None,
        respect_sustain=True,
        debug=False,
        channel=None,
        idle_failsafe_sec=2.0,
    ):
        """
        midi_input: BaseInput | int index | str (exact/substring) | None
        channel: 0-15 to filter messages. None = all channels.
        respect_sustain: honor CC64. Set False to rule out pedal-caused hangs.
        idle_failsafe_sec: if >0, auto-release all notes after this idle time
                           when no keys are physically held and sustain is false.
        """
        if backend:
            mido.set_backend(backend)

        self.SR = int(samplerate)
        self.blocksize = int(blocksize)
        self.MASTER_GAIN = float(master_gain)
        self.attack_step = 1.0 / max(1, int(self.SR * attack_ms / 1000))
        self.release_step = 1.0 / max(1, int(self.SR * release_ms / 1000))

        self._notes = {}  # note -> dict(phase,freq,ramp,step,gain)
        self._held_keys = set()  # keys physically down
        self._sustain = False
        self._respect_sustain = bool(respect_sustain)
        self._debug = bool(debug)
        self._channel = channel
        self._idle_failsafe_sec = float(idle_failsafe_sec)
        self._last_msg_ts = time.time()

        self._lock = threading.Lock()
        self._listener_th = None
        self._stop_evt = threading.Event()
        self._inport = None
        self._owns_port = False
        self._audio = None

        midi_input = mido.open_input(
            interface
        )  # TODO button to iterate over detected interfaces

        # Resolve input
        if isinstance(midi_input, mido.ports.BaseInput):
            self._inport = midi_input
            self._owns_port = False
            self.port_name = getattr(midi_input, "name", "external-input")
        else:
            ins = mido.get_input_names()
            if not ins:
                raise RuntimeError("No MIDI input devices found.")
            if isinstance(midi_input, int):
                self.port_name = ins[midi_input]
            elif isinstance(midi_input, str):
                self.port_name = next(
                    (n for n in ins if midi_input.lower() in n.lower()), None
                )
                if self.port_name is None:
                    raise RuntimeError(
                        f"No MIDI input matching '{midi_input}'. Found: {ins}"
                    )
            else:
                self.port_name = ins[0]
            self._inport = mido.open_input(self.port_name)
            self._owns_port = True

        self.start()

    @staticmethod
    def midi_to_freq(n):
        return 440.0 * (2.0 ** ((n - 69) / 12.0))

    # ---------- MIDI handling ----------
    def _ch_ok(self, msg):
        return (self._channel is None) or (
            getattr(msg, "channel", None) == self._channel
        )

    def _note_on(self, n, vel):
        with self._lock:
            self._held_keys.add(n)
            st = self._notes.get(n)
            g = (vel / 127.0) * self.MASTER_GAIN
            if st is None:
                self._notes[n] = {
                    "phase": 0.0,
                    "freq": self.midi_to_freq(n),
                    "ramp": 0.0,
                    "step": self.attack_step,
                    "gain": g,
                }
            else:
                st["step"] = self.attack_step
                st["gain"] = g

    def _note_off(self, n):
        with self._lock:
            self._held_keys.discard(n)
            if self._respect_sustain and self._sustain:
                return
            if n in self._notes:
                self._notes[n]["step"] = -self.release_step

    def _all_notes_off(self):
        with self._lock:
            for st in self._notes.values():
                st["step"] = -self.release_step
            self._held_keys.clear()

    def _handle_cc(self, control, value):
        if control == 64 and self._respect_sustain:  # sustain
            sustain_now = value >= 64
            if self._debug:
                print(f"[CC64] value={value} sustain={sustain_now}")
            if self._sustain and not sustain_now:
                with self._lock:
                    for n, st in list(self._notes.items()):
                        if n not in self._held_keys:
                            st["step"] = -self.release_step
            self._sustain = sustain_now
        elif control in (120, 123):  # All Sound Off / All Notes Off
            if self._debug:
                print(f"[CC{control}] panic")
            self._all_notes_off()

    def _midi_loop(self):
        if self._debug:
            print(f"[MIDI] Listening on: {self.port_name}")
        for msg in self._inport:
            if self._stop_evt.is_set():
                break
            self._last_msg_ts = time.time()
            if not self._ch_ok(msg):
                continue

            if msg.type == "note_on":
                if msg.velocity == 0:
                    if self._debug:
                        print(f"[MIDI] note_off via note_on0 n={msg.note}")
                    self._note_off(msg.note)
                else:
                    if self._debug:
                        print(f"[MIDI] note_on n={msg.note} v={msg.velocity}")
                    self._note_on(msg.note, msg.velocity)
            elif msg.type == "note_off":
                if self._debug:
                    print(f"[MIDI] note_off n={msg.note}")
                self._note_off(msg.note)
            elif msg.type == "control_change":
                self._handle_cc(msg.control, msg.value)
            elif self._debug and msg.type not in ("active_sensing", "clock"):
                print(f"[MIDI] {msg}")

    # ---------- Audio ----------
    def _audio_cb(self, outdata, frames, time_info, status):
        # idle failsafe: fade out if nothing is held and sustain is off and idle too long
        if self._idle_failsafe_sec > 0:
            if (
                (not self._sustain)
                and (len(self._held_keys) == 0)
                and (time.time() - self._last_msg_ts > self._idle_failsafe_sec)
            ):
                self._all_notes_off()

        buf = np.zeros(frames, dtype=np.float32)
        with self._lock:
            active = list(self._notes.items())
        if active:
            for note, st in active:
                phase, w = st["phase"], 2.0 * math.pi * st["freq"] / self.SR
                ramp, step, gain = st["ramp"], st["step"], st["gain"]
                s = np.empty(frames, dtype=np.float32)
                p, r = phase, ramp
                for i in range(frames):
                    r = min(1.0, max(0.0, r + step))
                    s[i] = math.sin(p) * (r * gain)
                    p += w
                    if p > 2.0 * math.pi:
                        p -= 2.0 * math.pi
                buf += s
                st["phase"], st["ramp"] = p, r
            with self._lock:
                for n in [
                    n
                    for n, st in self._notes.items()
                    if st["ramp"] <= 0.0 and st["step"] < 0
                ]:
                    del self._notes[n]
        outdata[:] = buf.reshape(-1, 1)

    # ---------- Lifecycle ----------
    def start(self):
        if self._audio is not None:
            return
        self._stop_evt.clear()
        self._listener_th = threading.Thread(target=self._midi_loop, daemon=True)
        self._listener_th.start()
        self._audio = sd.OutputStream(
            channels=1,
            callback=self._audio_cb,
            samplerate=self.SR,
            blocksize=self.blocksize,
            dtype="float32",
        )
        self._audio.start()
        # if self._debug:
        print("[AUDIO] started")

    def stop(self):
        self._stop_evt.set()
        if self._audio is not None:
            self._audio.stop()
            self._audio.close()
            self._audio = None
        if self._listener_th is not None:
            self._listener_th.join(timeout=1.0)
            self._listener_th = None
        if self._owns_port and self._inport is not None:
            self._inport.close()
            self._inport = None
        # if self._debug:
            print("[AUDIO] stopped")

    def panic(self):
        self._all_notes_off()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.stop()


if __name__ == "__main__":
    pressed = {}
    interfaces = mido.get_input_names()
    inport = mido.open_input(
        interfaces[1]
    )  # TODO button to iterate over detected interfaces
    synth = SineMIDISynth(midi_input=inport, respect_sustain=True)

    synth.start()
    while True:
        time.sleep(0.1)

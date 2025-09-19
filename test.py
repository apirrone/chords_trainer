# simple_sine_midi.py
import argparse, threading, math
import numpy as np
import sounddevice as sd
import mido

SR = 48000
MASTER_GAIN = 0.2
ATTACK_MS, RELEASE_MS = 5, 30
attack_step  = 1.0 / max(1, int(SR * ATTACK_MS  / 1000))
release_step = 1.0 / max(1, int(SR * RELEASE_MS / 1000))

notes = {}
lock = threading.Lock()

def midi_to_freq(n): return 440.0 * (2.0 ** ((n - 69) / 12.0))

def pick_port(index=None, match=None):
    ins = mido.get_input_names()
    if not ins: raise RuntimeError("No MIDI input devices found.")
    if index is not None:
        return ins[index]
    if match:
        for name in ins:
            if match.lower() in name.lower():
                return name
        raise RuntimeError(f"No MIDI input matching '{match}'. Found: {ins}")
    return ins[0]

def midi_listener(port_name):
    with mido.open_input(port_name) as port:
        for msg in port:
            if msg.type in ("note_on", "note_off"):
                n = msg.note
                vel = msg.velocity if msg.type == "note_on" else 0
                with lock:
                    if vel > 0:
                        notes.setdefault(n, {
                            "phase": 0.0, "freq": midi_to_freq(n),
                            "ramp": 0.0, "step": attack_step,
                            "gain": (vel / 127.0) * MASTER_GAIN
                        })
                        st = notes[n]
                        st["step"] = attack_step
                        st["gain"] = (vel / 127.0) * MASTER_GAIN
                    elif n in notes:
                        notes[n]["step"] = -release_step
            elif msg.type == "control_change" and msg.control == 123:  # All Notes Off
                with lock:
                    for st in notes.values(): st["step"] = -release_step

def audio_callback(outdata, frames, time, status):
    buf = np.zeros(frames, dtype=np.float32)
    with lock: active = list(notes.items())
    if active:
        for note, st in active:
            phase, w = st["phase"], 2.0 * math.pi * st["freq"] / SR
            ramp, step, gain = st["ramp"], st["step"], st["gain"]
            s = np.empty(frames, dtype=np.float32)
            p, r = phase, ramp
            for i in range(frames):
                r = min(1.0, max(0.0, r + step))
                s[i] = math.sin(p) * (r * gain)
                p += w
                if p > 2.0 * math.pi: p -= 2.0 * math.pi
            buf += s
            st["phase"], st["ramp"] = p, r
        with lock:
            for n in [n for n, st in notes.items() if st["ramp"] <= 0.0 and st["step"] < 0]:
                del notes[n]
    outdata[:] = buf.reshape(-1, 1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port-index", type=int, help="Index from mido.get_input_names()")
    parser.add_argument("--port-match", type=str, help="Substring to match device name")
    parser.add_argument("--samplerate", type=int, default=SR)
    parser.add_argument("--blocksize", type=int, default=256)
    args = parser.parse_args()

    # Optional explicit backend if needed:
    # mido.set_backend('mido.backends.rtmidi')

    ins = mido.get_input_names()
    print("Detected MIDI inputs:")
    for i, name in enumerate(ins): print(f"{i}: {name}")

    port_name = pick_port(args.port_index, args.port_match)
    print("Using MIDI input:", port_name)

    t = threading.Thread(target=midi_listener, args=(port_name,), daemon=True)
    t.start()

    with sd.OutputStream(channels=1, callback=audio_callback,
                         samplerate=args.samplerate, blocksize=args.blocksize, dtype="float32"):
        print("Ready. Ctrl+C to quit.")
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    main()

# Chords Trainer

A python app that helps you train your chords on the piano (or any midi instrument actually).

## Installation

```bash
$ pip install -e .
```

## Usage

I'll add something to make it easier to select the relevant midi interface at some point. For now, you'll have to change the value in `__init__.py` :

```python
inport = mido.open_input(interfaces[1]) # This value (1)
```

Then run:

```bash
$ chords-trainer
```

You can click on the `train mode` button to switch to train mode. In this mode, the app shows you a random chord, if you play the right chord it goes to a next one.

Click on the "difficulty" button to change it. It's a number between 0 and 2. 0 is easiest, 2 is hardest.


## TODO
- [X] Add a way to select the midi interface (just a button to iterate over interfaces)
- [X] Add a way to change the difficulty in the app
- [ ] Show a keyboard on the bottom of the UI
- [ ] Include flat notes
- [ ] Improve train mode
  - [ ] Make "train sessions", with stats (reactivity, errors)
  - [x] Make a training program Anki style
  - [ ] Identify chords inversions played, encourage variety
  - [ ] Vary abbreviations
  - [ ] More difficulty granularity ?
  - [ ] Click to show solution
  - [ ] 
- [ ] Config file for defaults (start in train mode, prefered interface ...)


## Notes

### Message attributes
- msg.type
- msg.note
- msg.velocity
- msg.channel

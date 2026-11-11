# Voice Assistant: open any program by name

A small Python assistant for Windows that opens any installed program when you say or
type its name. It reads your Start Menu, so it knows every app you have without any
setup, and it forgives typos and partial names.

```
> open spotfy
Opening Spotify.
> visual studio
Opening Visual Studio Code.
> launch my steam please
Opening Steam.
```

## Run

Needs Windows and Python 3.9 or newer. Typed mode needs no packages.

```bash
python assistant.py            # type app names
python assistant.py --list     # see every app it found
```

### Voice mode

```bash
pip install -r requirements-voice.txt
python assistant.py --voice
```

Voice mode uses your microphone, Google's free web speech recognizer (needs internet,
no key) and offline text-to-speech for replies. If a package or the microphone is
missing, it falls back to typing.

## How it matches names

1. Filler words go first: "please open the Spotify app" becomes "spotify".
2. An exact name wins.
3. Then names that start with what you said, shortest first ("steam" picks Steam over
   Steam Support Center).
4. Then names that contain all your words ("code" finds Visual Studio Code).
5. Then a fuzzy match for typos ("spotfy" finds Spotify).

Uninstallers, readmes and help links in the Start Menu are skipped.

## Test

```bash
pip install pytest
python -m pytest
```

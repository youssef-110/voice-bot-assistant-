"""Open any program on your PC by saying or typing its name.

Scans the Windows Start Menu for installed apps, matches what you said to the closest
name (typos and partial names work), and launches it.

    python assistant.py            type app names
    python assistant.py --voice    speak them (needs the voice extras, see README)
    python assistant.py --list     show every app it found
"""

from __future__ import annotations

import argparse
import difflib
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# Start Menu entries that are not apps people want to open by voice.
SKIP = re.compile(r"\b(uninstall|readme|help|documentation|release notes|license|website|manual)\b", re.I)
FILLER = re.compile(r"^(please\s+)?(open|launch|start|run|go to|show me)\s+(the\s+|my\s+)?|\s+(please|app|application|program)$", re.I)
BUILTINS = {
    # Windows apps without a Start Menu shortcut file.
    "settings": "ms-settings:",
    "calculator": "calc.exe",
    "notepad": "notepad.exe",
    "file explorer": "explorer.exe",
    "task manager": "taskmgr.exe",
    "command prompt": "cmd.exe",
}


@dataclass(frozen=True)
class App:
    name: str
    target: str  # a .lnk path, an .exe name or a URI that os.startfile accepts


def start_menu_dirs() -> list[Path]:
    dirs = []
    for env in ("ProgramData", "APPDATA"):
        base = os.environ.get(env)
        if base:
            dirs.append(Path(base) / "Microsoft" / "Windows" / "Start Menu" / "Programs")
    return [d for d in dirs if d.is_dir()]


def scan(dirs: list[Path] | None = None) -> list[App]:
    """Every Start Menu shortcut plus a few built-ins, one entry per name."""
    found: dict[str, App] = {name: App(name, target) for name, target in BUILTINS.items()}
    for root in start_menu_dirs() if dirs is None else dirs:
        for link in root.rglob("*"):
            if link.suffix.lower() not in (".lnk", ".url", ".appref-ms"):
                continue
            name = link.stem.strip()
            if SKIP.search(name):
                continue
            found.setdefault(name.lower(), App(name, str(link)))
    return sorted(found.values(), key=lambda a: a.name.lower())


def clean(request: str) -> str:
    """'please open the spotify app' -> 'spotify'."""
    text = request.strip().lower()
    previous = None
    while previous != text:
        previous, text = text, FILLER.sub("", text).strip()
    return text


def find(request: str, apps: list[App]) -> list[App]:
    """Best matches first: exact name, then names starting with or containing the words, then fuzzy."""
    query = clean(request)
    if not query:
        return []
    by_name = {a.name.lower(): a for a in apps}
    if query in by_name:
        return [by_name[query]]

    starts = [a for a in apps if a.name.lower().startswith(query)]
    words = query.split()
    contains = [a for a in apps if a not in starts and all(w in a.name.lower() for w in words)]
    ranked = sorted(starts, key=lambda a: len(a.name)) + sorted(contains, key=lambda a: len(a.name))
    if ranked:
        return ranked[:5]

    close = difflib.get_close_matches(query, list(by_name), n=5, cutoff=0.6)
    return [by_name[c] for c in close]


def launch(app: App) -> None:
    if sys.platform != "win32":
        raise OSError("Launching apps only works on Windows.")
    os.startfile(app.target)  # noqa: S606 - targets come from the user's own Start Menu


class Voice:
    """Optional speech in and out. Imported lazily so typed mode needs no extra packages."""

    def __init__(self) -> None:
        import pyttsx3
        import speech_recognition as sr

        self.sr = sr
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone()
        self.tts = pyttsx3.init()
        with self.mic as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

    def say(self, text: str) -> None:
        self.tts.say(text)
        self.tts.runAndWait()

    def listen(self) -> str | None:
        with self.mic as source:
            audio = self.recognizer.listen(source, phrase_time_limit=5)
        try:
            # Google's free web recognizer: needs internet, no key.
            return self.recognizer.recognize_google(audio)
        except (self.sr.UnknownValueError, self.sr.RequestError):
            return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Open any program on your PC by name.")
    parser.add_argument("--voice", action="store_true", help="speak instead of typing")
    parser.add_argument("--list", action="store_true", help="list every app found and exit")
    args = parser.parse_args()

    apps = scan()
    if args.list:
        for app in apps:
            print(app.name)
        print(f"\n{len(apps)} apps")
        return

    voice = None
    if args.voice:
        try:
            voice = Voice()
        except Exception as exc:  # missing packages or no microphone
            print(f"Voice mode unavailable ({exc}). Falling back to typing.")

    def say(text: str) -> None:
        print(text)
        if voice:
            voice.say(text)

    say(f"I found {len(apps)} apps. Which one should I open? Say 'quit' to stop.")
    while True:
        if voice:
            print("Listening...")
            heard = voice.listen()
            if heard is None:
                print("(didn't catch that)")
                continue
            print(f"You: {heard}")
        else:
            try:
                heard = input("> ")
            except EOFError:
                return
        if clean(heard) in ("quit", "exit", "stop", "goodbye", "bye"):
            say("Goodbye!")
            return

        matches = find(heard, apps)
        if not matches:
            say(f"I couldn't find an app called {clean(heard)}.")
            continue
        app = matches[0]
        try:
            launch(app)
            say(f"Opening {app.name}.")
        except OSError as exc:
            say(f"I couldn't open {app.name}: {exc}")
        if len(matches) > 1:
            print("  Other matches: " + ", ".join(m.name for m in matches[1:]))


if __name__ == "__main__":
    main()

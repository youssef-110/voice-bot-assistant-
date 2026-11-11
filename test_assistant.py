from pathlib import Path

import assistant
from assistant import App, clean, find, scan


def make_start_menu(tmp_path: Path) -> Path:
    for rel in [
        "Google Chrome.lnk",
        "Spotify.lnk",
        "Visual Studio Code/Visual Studio Code.lnk",
        "Visual Studio Code/Uninstall Visual Studio Code.lnk",
        "Steam/Steam.lnk",
        "Steam/Steam Support Center.url",
        "OBS Studio/OBS Studio (64bit).lnk",
        "notes.txt",
    ]:
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("")
    return tmp_path


def test_scan_finds_shortcuts_and_skips_uninstallers(tmp_path):
    names = [a.name for a in scan([make_start_menu(tmp_path)])]
    assert "Spotify" in names and "Visual Studio Code" in names and "Steam Support Center" in names
    assert not any("Uninstall" in n for n in names)
    assert "notes" not in names
    assert "calculator" in names  # built-ins are always there


def test_clean_strips_filler_words():
    assert clean("Please open the Spotify app") == "spotify"
    assert clean("launch my steam") == "steam"
    assert clean("start notepad please") == "notepad"


def test_find_prefers_exact_then_prefix_then_contains(tmp_path):
    apps = scan([make_start_menu(tmp_path)])
    assert find("open steam", apps)[0].name == "Steam"
    assert find("visual studio", apps)[0].name == "Visual Studio Code"
    assert find("obs", apps)[0].name == "OBS Studio (64bit)"
    assert find("code", apps)[0].name == "Visual Studio Code"


def test_find_handles_typos(tmp_path):
    apps = scan([make_start_menu(tmp_path)])
    assert find("open spotfy", apps)[0].name == "Spotify"
    assert find("stem", apps)[0].name == "Steam"


def test_find_returns_nothing_for_nonsense(tmp_path):
    apps = scan([make_start_menu(tmp_path)])
    assert find("open xylophone quantum", apps) == []
    assert find("open", apps) == []


def test_launch_uses_startfile(monkeypatch):
    opened = []
    monkeypatch.setattr(assistant.sys, "platform", "win32")
    monkeypatch.setattr(assistant.os, "startfile", opened.append, raising=False)
    assistant.launch(App("Notepad", "notepad.exe"))
    assert opened == ["notepad.exe"]

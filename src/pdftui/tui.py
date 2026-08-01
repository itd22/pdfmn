from __future__ import annotations

import curses
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from . import db_bridge, json_bridge, yaml_bridge
from .books_lib import BooksSpine, POLICIES

SETTINGS_FILE = ".pdftui_tui_settings.json"

SETTINGS_FIELDS = (
    "policy",
    "top_dir",
    "main_json",
    "merged_json",
    "main_yaml",
    "saved_yaml",
    "yaml_input_path",
)

MAIN_MENU = [
    ("Load", "load"),
    ("Crawl && Merge", "crawl_and_merge"),
    ("Save", "save"),
    ("Save as JSON", "save_as_json"),
    ("Save as YAML", "save_as_yaml"),
    ("Save as DB", "save_as_db"),
    ("Show entries", "show_entries"),
    ("Settings", "settings"),
    ("Save settings to file", "save_settings"),
    ("Quit", "quit"),
]


def load_saved_settings(path: str = SETTINGS_FILE) -> dict:
    """Read previously-saved TUI settings from disk. Missing/invalid file -> {}."""
    p = Path(path)
    if not p.exists():
        return {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    return {k: raw[k] for k in SETTINGS_FIELDS if k in raw}


@dataclass
class TuiSession:
    """Holds everything the TUI needs across repeated actions.

    This object is created once per TUI run and never discarded between
    actions -- Load / Crawl & Merge / Save / Settings all read and write
    the same session, so parameters and the in-memory entry list survive
    from one action to the next until the user explicitly changes them
    or quits.
    """

    policy: str = "json"
    top_dir: str = ""
    main_json: str = "main.json"
    merged_json: str = "merged.json"
    main_yaml: str = "main.yaml"
    saved_yaml: str = "saved.yaml"
    yaml_input_path: str = ""
    lib: Optional[BooksSpine] = None
    last_message: str = "Welcome. Pick an action."

    def get_lib(self) -> BooksSpine:
        """Return the BooksSpine for the current policy, building it (with
        the current paths) only if it doesn't exist yet or the policy
        changed -- never as a side effect of running an action, so the
        in-memory entries survive repeated Load / Crawl & Merge / Save
        calls."""
        if self.lib is None or self.lib.policy != self.policy:
            self.lib = BooksSpine(
                policy=self.policy,
                json_path=self.main_json,
                merged_json_path=self.merged_json,
                yaml_path=self.main_yaml,
                saved_yaml_path=self.saved_yaml,
                yaml_input_path=self.yaml_input_path or self.top_dir,
            )
        else:
            # keep paths in sync in case Settings changed them since load
            self.lib.json_path = self.main_json
            self.lib.merged_json_path = self.merged_json
            self.lib.yaml_path = self.main_yaml
            self.lib.saved_yaml_path = self.saved_yaml
            self.lib.yaml_input_path = self.yaml_input_path or self.top_dir
        return self.lib

    def settings_fields(self) -> List[tuple]:
        return [
            ("policy", "Policy (json/yaml/db)", self.policy),
            ("top_dir", "Top dir to crawl", self.top_dir),
            ("main_json", "main.json path (json policy load source)", self.main_json),
            ("merged_json", "merged.json output path (json policy save dest)", self.merged_json),
            ("main_yaml", "main.yaml path (yaml policy load source)", self.main_yaml),
            ("saved_yaml", "saved.yaml output path (yaml policy save dest)", self.saved_yaml),
            ("yaml_input_path", "yaml input_path header (blank = top_dir)", self.yaml_input_path),
        ]

    def settings_dict(self) -> dict:
        return {field_name: getattr(self, field_name) for field_name in SETTINGS_FIELDS}


def save_saved_settings(session: "TuiSession", path: str = SETTINGS_FILE) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(session.settings_dict(), f, indent=2, ensure_ascii=False)


def _draw_header(win, session: TuiSession, max_x: int) -> None:
    entry_count = len(session.lib.shelf.books) if session.lib else 0
    header = f" pdftui TUI | policy={session.policy} | entries in memory: {entry_count} "
    win.addnstr(0, 0, header.ljust(max_x), max_x, curses.A_REVERSE)


def _draw_footer(win, session: TuiSession, max_y: int, max_x: int) -> None:
    win.addnstr(max_y - 1, 0, session.last_message.ljust(max_x)[: max_x - 1], max_x - 1, curses.A_DIM)


def _prompt(stdscr, prompt: str, initial: str = "") -> str:
    """Editable text prompt with a real line editor: Backspace/Delete only
    ever touch the characters the user is editing (never the surrounding
    window content), so the existing value can be fully replaced -- not
    just appended to."""
    max_y, max_x = stdscr.getmaxyx()
    win = curses.newwin(3, max_x, max_y - 4, 0)
    win.keypad(True)

    buf = list(initial)
    cursor = len(buf)

    def redraw():
        win.erase()
        win.border()
        win.addnstr(0, 2, f" {prompt} (Enter=confirm, Esc=cancel) ", max_x - 4)
        text = "".join(buf)
        win.addnstr(1, 2, f"> {text}", max_x - 5)
        win.move(1, min(4 + cursor, max_x - 2))
        win.refresh()

    curses.curs_set(1)
    redraw()
    try:
        while True:
            ch = win.getch()
            if ch in (curses.KEY_ENTER, ord("\n"), ord("\r")):
                break
            elif ch == 27:  # ESC -- cancel, keep the original value
                buf = list(initial)
                break
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                if cursor > 0:
                    del buf[cursor - 1]
                    cursor -= 1
            elif ch == curses.KEY_DC:  # Delete
                if cursor < len(buf):
                    del buf[cursor]
            elif ch == curses.KEY_LEFT:
                cursor = max(0, cursor - 1)
            elif ch == curses.KEY_RIGHT:
                cursor = min(len(buf), cursor + 1)
            elif ch == curses.KEY_HOME:
                cursor = 0
            elif ch == curses.KEY_END:
                cursor = len(buf)
            elif 0 <= ch < 256 and chr(ch).isprintable():
                buf.insert(cursor, chr(ch))
                cursor += 1
            redraw()
    finally:
        curses.curs_set(0)

    text = "".join(buf)
    return text if text else initial


def _select_from(stdscr, title: str, items: List[str], start_index: int = 0) -> Optional[int]:
    """Simple arrow-key menu. Returns selected index, or None if the user
    backed out with 'q'/ESC."""
    idx = start_index
    exceed_screen_max = False
    scrolled_delta =0
    scrolled_index = 0
    max_x = 0
    while True:
        stdscr.erase()
        max_y, max_x = stdscr.getmaxyx()
        stdscr.addnstr(0, 0, title, max_x - 1, curses.A_BOLD)
        for i, item in enumerate(items):
            scrolled_index = i - scrolled_delta
            if scrolled_index < 0:
                continue
            attr = curses.A_REVERSE if scrolled_index == idx else curses.A_NORMAL
            stdscr.addnstr(2 + scrolled_index, 2, item, max_x - 3, attr)
            if scrolled_index > max_y - 4:
                exceed_screen_max = True
                break
            
        stdscr.addnstr(max_y - 1, 0, "Up/Down or j/k to move, Enter to select, q to go back", max_x - 1, curses.A_DIM)
        stdscr.refresh()

        key = stdscr.getch()
        if key in (curses.KEY_UP, ord("k")):
            idx = (idx - 1) % len(items)
            if scrolled_delta > 0 and idx - scrolled_delta < 2:
                scrolled_delta -= 1
                idx = (idx + 1) % len(items)  
                
        elif key in (curses.KEY_DOWN, ord("j")):
            idx = (idx + 1) % len(items)
            if exceed_screen_max and idx - scrolled_delta > max_y - 4 :
                scrolled_delta += 1
                exceed_screen_max = False
 
        elif key in (curses.KEY_ENTER, ord("\n"), ord("\r")):
            return idx
        elif key in (ord("q"), 27):  # 27 = ESC
            return None


def _action_load(stdscr, session: TuiSession) -> None:
    lib = session.get_lib()
    lib.load()
    session.last_message = f"Loaded {len(lib.shelf.books)} entries (policy={session.policy})."


def _action_crawl_and_merge(stdscr, session: TuiSession) -> None:
    top_dir = _prompt(stdscr, "Top directory to crawl", session.top_dir)
    if not top_dir:
        session.last_message = "Crawl & Merge cancelled: no top-dir given."
        return
    session.top_dir = top_dir

    lib = session.get_lib()
    crawled = lib.crawl_and_merge(top_dir)
    session.last_message = (
        f"Crawled {len(crawled)} PDF(s) under '{top_dir}', "
        f"library now has {len(lib.shelf.books)} entries."
    )


def _action_save(stdscr, session: TuiSession) -> None:
    lib = session.get_lib()
    lib.save()
    dest = {"json": session.merged_json, "yaml": session.saved_yaml, "db": "books_db.sqlite"}[session.policy]
    session.last_message = f"Saved {len(lib.shelf.books)} entries (policy={session.policy}) -> {dest}."


def _current_entries(session: TuiSession):
    return session.lib.shelf.books if session.lib else []


def _action_save_as_json(stdscr, session: TuiSession) -> None:
    entries = _current_entries(session)
    if not entries:
        session.last_message = "Nothing to save -- Load or Crawl & Merge first."
        return
    json_bridge.save(session.merged_json, entries)
    session.last_message = (
        f"Saved {len(entries)} entries as JSON -> {session.merged_json} "
        f"(independent of current policy={session.policy})."
    )


def _action_save_as_yaml(stdscr, session: TuiSession) -> None:
    entries = _current_entries(session)
    if not entries:
        session.last_message = "Nothing to save -- Load or Crawl & Merge first."
        return
    yaml_bridge.save(session.yaml_input_path or session.top_dir, entries, session.saved_yaml)
    session.last_message = (
        f"Saved {len(entries)} entries as YAML -> {session.saved_yaml} "
        f"(independent of current policy={session.policy})."
    )


def _action_save_as_db(stdscr, session: TuiSession) -> None:
    entries = _current_entries(session)
    if not entries:
        session.last_message = "Nothing to save -- Load or Crawl & Merge first."
        return
    if not db_bridge.is_exist():
        db_bridge.create_db()
    added = db_bridge.merge_to_db(entries)
    session.last_message = (
        f"Merged {len(entries)} entries into books_db.sqlite, {added} new "
        f"(independent of current policy={session.policy})."
    )


def _action_show_entries(stdscr, session: TuiSession) -> None:
    lib = session.get_lib()
    lines = [f"{e.name[0:20]}  |  {e.title[0:30] or '(no title)'}  |  {e.author[0:40]}" for e in lib.shelf.books if len(e.title)>0]
    if not lines:
        lines = ["(no entries loaded -- try Load or Crawl & Merge first)"]
    _select_from(stdscr, f"Entries ({len(lib.shelf.books)}) -- q to go back", lines, 0)


def _action_settings(stdscr, session: TuiSession) -> None:
    while True:
        fields = session.settings_fields()
        labels = [f"{label}: {value}" for _key, label, value in fields] + ["Back"]
        choice = _select_from(stdscr, "Settings -- Enter to edit a field", labels, 0)
        if choice is None or choice == len(fields):
            return

        key, label, value = fields[choice]
        if key == "policy":
            new_val = _select_from(stdscr, "Choose policy", list(POLICIES), POLICIES.index(session.policy))
            if new_val is not None:
                session.policy = POLICIES[new_val]
                session.last_message = f"Policy set to '{session.policy}'."
        else:
            new_val = _prompt(stdscr, label, value)
            setattr(session, key, new_val)
            session.last_message = f"{label} set to '{new_val}'."


def _action_save_settings(stdscr, session: TuiSession) -> None:
    save_saved_settings(session)
    session.last_message = f"Settings saved to '{SETTINGS_FILE}' (will auto-load next start)."


ACTION_HANDLERS = {
    "load": _action_load,
    "crawl_and_merge": _action_crawl_and_merge,
    "save": _action_save,
    "save_as_json": _action_save_as_json,
    "save_as_yaml": _action_save_as_yaml,
    "save_as_db": _action_save_as_db,
    "show_entries": _action_show_entries,
    "settings": _action_settings,
    "save_settings": _action_save_settings,
}


def _main_loop(stdscr, session: TuiSession) -> None:
    curses.curs_set(0)
    idx = 0
    labels = [label for label, _key in MAIN_MENU]

    while True:
        stdscr.erase()
        max_y, max_x = stdscr.getmaxyx()
        _draw_header(stdscr, session, max_x)
        for i, label in enumerate(labels):
            attr = curses.A_REVERSE if i == idx else curses.A_NORMAL
            stdscr.addnstr(2 + i, 2, label, max_x - 3, attr)
        _draw_footer(stdscr, session, max_y, max_x)
        stdscr.refresh()

        key = stdscr.getch()
        if key in (curses.KEY_UP, ord("k")):
            idx = (idx - 1) % len(labels)
        elif key in (curses.KEY_DOWN, ord("j")):
            idx = (idx + 1) % len(labels)
        elif key in (ord("q"), 27):
            return
        elif key in (curses.KEY_ENTER, ord("\n"), ord("\r")):
            _, action_key = MAIN_MENU[idx]
            if action_key == "quit":
                return
            handler = ACTION_HANDLERS[action_key]
            try:
                handler(stdscr, session)
            except Exception as exc:  # keep the TUI alive on action errors
                session.last_message = f"Error: {exc}"


def run_tui(
    top_dir: str = "",
    main_json: str = "main.json",
    merged_json: str = "merged.json",
    main_yaml: str = "main.yaml",
    saved_yaml: str = "saved.yaml",
    yaml_input_path: str = "",
) -> None:
    session = TuiSession(
        top_dir=top_dir or "",
        main_json=main_json,
        merged_json=merged_json,
        main_yaml=main_yaml,
        saved_yaml=saved_yaml,
        yaml_input_path=yaml_input_path or "",
    )

    saved = load_saved_settings()
    if saved:
        for key, value in saved.items():
            setattr(session, key, value)
        # an explicit --top-dir on the command line still wins over a saved one
        if top_dir:
            session.top_dir = top_dir
        session.last_message = f"Loaded settings from '{SETTINGS_FILE}'."

    curses.wrapper(_main_loop, session)

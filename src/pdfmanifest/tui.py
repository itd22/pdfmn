from __future__ import annotations

import curses
from dataclasses import dataclass, field
from typing import List, Optional

from .books_lib import BooksLib, POLICIES

MAIN_MENU = [
    ("Load", "load"),
    ("Crawl && Merge", "crawl_and_merge"),
    ("Save", "save"),
    ("Show entries", "show_entries"),
    ("Settings", "settings"),
    ("Quit", "quit"),
]


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
    lib: Optional[BooksLib] = None
    last_message: str = "Welcome. Pick an action."

    def get_lib(self) -> BooksLib:
        """Return the BooksLib for the current policy, building it (with
        the current paths) only if it doesn't exist yet or the policy
        changed -- never as a side effect of running an action, so the
        in-memory entries survive repeated Load / Crawl & Merge / Save
        calls."""
        if self.lib is None or self.lib.policy != self.policy:
            self.lib = BooksLib(
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
            ("main_json", "main.json path", self.main_json),
            ("merged_json", "merged.json output path", self.merged_json),
            ("main_yaml", "main.yaml path", self.main_yaml),
            ("saved_yaml", "saved.yaml output path", self.saved_yaml),
            ("yaml_input_path", "yaml input_path header (blank = top_dir)", self.yaml_input_path),
        ]


def _draw_header(win, session: TuiSession, max_x: int) -> None:
    entry_count = len(session.lib.entries) if session.lib else 0
    header = f" pdfmanifest TUI | policy={session.policy} | entries in memory: {entry_count} "
    win.addnstr(0, 0, header.ljust(max_x), max_x, curses.A_REVERSE)


def _draw_footer(win, session: TuiSession, max_y: int, max_x: int) -> None:
    win.addnstr(max_y - 1, 0, session.last_message.ljust(max_x)[: max_x - 1], max_x - 1, curses.A_DIM)


def _prompt(stdscr, prompt: str, initial: str = "") -> str:
    max_y, max_x = stdscr.getmaxyx()
    win = curses.newwin(3, max_x, max_y - 4, 0)
    win.border()
    win.addnstr(0, 2, f" {prompt} ", max_x - 4)
    win.addnstr(1, 2, f"> {initial}", max_x - 4)
    win.refresh()

    curses.echo()
    curses.curs_set(1)
    try:
        raw = win.getstr(1, 4 + len(initial))
        text = raw.decode("utf-8") if raw else ""
    finally:
        curses.noecho()
        curses.curs_set(0)

    return text if text else initial


def _select_from(stdscr, title: str, items: List[str], start_index: int = 0) -> Optional[int]:
    """Simple arrow-key menu. Returns selected index, or None if the user
    backed out with 'q'/ESC."""
    idx = start_index
    while True:
        stdscr.erase()
        max_y, max_x = stdscr.getmaxyx()
        stdscr.addnstr(0, 0, title, max_x - 1, curses.A_BOLD)
        for i, item in enumerate(items):
            attr = curses.A_REVERSE if i == idx else curses.A_NORMAL
            stdscr.addnstr(2 + i, 2, item, max_x - 3, attr)
        stdscr.addnstr(max_y - 1, 0, "Up/Down or j/k to move, Enter to select, q to go back", max_x - 1, curses.A_DIM)
        stdscr.refresh()

        key = stdscr.getch()
        if key in (curses.KEY_UP, ord("k")):
            idx = (idx - 1) % len(items)
        elif key in (curses.KEY_DOWN, ord("j")):
            idx = (idx + 1) % len(items)
        elif key in (curses.KEY_ENTER, ord("\n"), ord("\r")):
            return idx
        elif key in (ord("q"), 27):  # 27 = ESC
            return None


def _action_load(stdscr, session: TuiSession) -> None:
    lib = session.get_lib()
    lib.load()
    session.last_message = f"Loaded {len(lib.entries)} entries (policy={session.policy})."


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
        f"library now has {len(lib.entries)} entries."
    )


def _action_save(stdscr, session: TuiSession) -> None:
    lib = session.get_lib()
    lib.save()
    dest = {"json": session.merged_json, "yaml": session.saved_yaml, "db": "books_db.sqlite"}[session.policy]
    session.last_message = f"Saved {len(lib.entries)} entries (policy={session.policy}) -> {dest}."


def _action_show_entries(stdscr, session: TuiSession) -> None:
    lib = session.get_lib()
    lines = [f"{e.name}  |  {e.title or '(no title)'}  |  {e.file}" for e in lib.entries]
    if not lines:
        lines = ["(no entries loaded -- try Load or Crawl & Merge first)"]
    _select_from(stdscr, f"Entries ({len(lib.entries)}) -- q to go back", lines, 0)


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


ACTION_HANDLERS = {
    "load": _action_load,
    "crawl_and_merge": _action_crawl_and_merge,
    "save": _action_save,
    "show_entries": _action_show_entries,
    "settings": _action_settings,
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
    curses.wrapper(_main_loop, session)

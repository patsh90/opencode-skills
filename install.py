#!/usr/bin/env python3
"""Interactive installer for the skills in this repository.

Tick the skills you want (or choose them on the command line) and install them
either into the current project (``./.opencode/skills/``) or globally
(``~/.config/opencode/skills/``).

Uses only the Python standard library. The interactive picker uses ``curses``
when a real terminal is available and falls back to a numbered prompt otherwise.

Examples
--------
    python3 install.py                     # checkbox picker, then pick a location
    python3 install.py --all               # every skill
    python3 install.py --skills project-steward,markdown-to-odt-letters
    python3 install.py --all --scope global
    python3 install.py --skills anki-card-reviewer --scope local --force
    python3 install.py --all --uninstall --scope global
    python3 install.py --list              # show what is available
"""

from __future__ import annotations

import argparse
import curses
import locale
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent

# Skipped when copying a skill into place.
IGNORE = shutil.ignore_patterns(
    "__pycache__", "*.pyc", "*.pyo", ".DS_Store", ".git", "*.swp", "*~"
)

SCOPES = ("local", "global")


# --------------------------------------------------------------------------- #
# Skill discovery
# --------------------------------------------------------------------------- #


@dataclass
class Skill:
    name: str
    source: Path
    description: str = ""


def _read_frontmatter(path: Path) -> dict:
    """Return the top-level ``key: value`` pairs of a SKILL.md frontmatter."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    meta: dict = {}
    for line in text[3:end].splitlines():
        if not line.strip() or line[0] in " \t#":
            continue
        key, sep, value = line.partition(":")
        if sep:
            meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta


def _find_skill_dir(base: Path):
    """A skill dir is either ``base`` itself or a single immediate subdir."""
    if (base / "SKILL.md").is_file():
        return base
    subdirs = sorted(
        p for p in base.iterdir() if p.is_dir() and (p / "SKILL.md").is_file()
    )
    if len(subdirs) == 1:
        return subdirs[0]
    return None


def discover_skills(repo_root: Path) -> list:
    skills = []
    for entry in sorted(repo_root.iterdir()):
        if entry.name.startswith(".") or not entry.is_dir():
            continue
        source = _find_skill_dir(entry)
        if source is None:
            continue
        meta = _read_frontmatter(source / "SKILL.md")
        skills.append(
            Skill(
                name=meta.get("name") or source.name,
                source=source,
                description=meta.get("description", ""),
            )
        )
    return skills


# --------------------------------------------------------------------------- #
# Destinations
# --------------------------------------------------------------------------- #


def scope_root(scope: str, target: str | None) -> Path:
    if target:
        return Path(target).expanduser().resolve()
    if scope == "global":
        xdg = os.environ.get("XDG_CONFIG_HOME")
        base = Path(xdg).expanduser() if xdg else Path.home() / ".config"
        return base / "opencode" / "skills"
    return Path.cwd() / ".opencode" / "skills"


# --------------------------------------------------------------------------- #
# Curses helpers
# --------------------------------------------------------------------------- #


def _can_use_curses() -> bool:
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except Exception:
        return False


def _addstr(stdscr, y: int, x: int, text: str, attr: int = 0) -> None:
    try:
        stdscr.addstr(y, x, text, attr)
    except curses.error:
        pass


def _clip(text: str, width: int) -> str:
    return text if len(text) <= width else text[: max(0, width - 1)] + "\u2026"


def _choose_skills_curses(stdscr, skills: list) -> list | None:
    curses.curs_set(0)
    try:
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
    except curses.error:
        pass
    highlight = curses.color_pair(1) if curses.has_colors() else curses.A_REVERSE

    selected = [False] * len(skills)
    cursor = 0
    top = 0  # first visible line, in item lines

    while True:
        stdscr.erase()
        height, width = stdscr.getmaxyx()
        body_top = 3
        visible = max(1, height - body_top - 2)

        _addstr(stdscr, 0, 0, "Select skills to install", curses.A_BOLD)
        _addstr(
            stdscr,
            1,
            0,
            "up/down move   space toggle   a all   n none   enter install   q quit",
            curses.A_DIM,
        )

        # Each skill occupies two lines: the checkbox line and a description.
        item_y = []
        y = 0
        for _ in skills:
            item_y.append(y)
            y += 2

        # Keep the cursor item in view.
        if item_y[cursor] < top:
            top = item_y[cursor]
        if item_y[cursor] + 1 >= top + visible:
            top = item_y[cursor] + 2 - visible

        for i, skill in enumerate(skills):
            row = item_y[i] - top
            if row < 0 or row >= visible:
                continue
            mark = "[x]" if selected[i] else "[ ]"
            pointer = "\u25b8 " if i == cursor else "  "
            line = f"{pointer}{mark} {skill.name}"
            attr = highlight if i == cursor else curses.A_NORMAL
            _addstr(stdscr, body_top + row, 0, _clip(line, width - 1), attr)
            _addstr(
                stdscr,
                body_top + row + 1,
                0,
                _clip("      " + skill.description, width - 1),
                curses.A_DIM,
            )

        footer = f" {sum(selected)} selected "
        _addstr(stdscr, height - 1, 0, footer.center(width), curses.A_DIM)
        stdscr.refresh()

        key = stdscr.getch()
        if key in (curses.KEY_UP, ord("k")):
            cursor = max(0, cursor - 1)
        elif key in (curses.KEY_DOWN, ord("j")):
            cursor = min(len(skills) - 1, cursor + 1)
        elif key == ord(" "):
            selected[cursor] = not selected[cursor]
        elif key == ord("a"):
            selected = [True] * len(skills)
        elif key == ord("n"):
            selected = [False] * len(skills)
        elif key in (curses.KEY_ENTER, 10, 13):
            if any(selected):
                return [skills[i] for i in range(len(skills)) if selected[i]]
        elif key in (ord("q"), 27):  # q or Esc
            return None


def _choose_scope_curses(stdscr, dest_local: Path, dest_global: Path) -> str | None:
    curses.curs_set(0)
    options = [
        ("local", "This project", str(dest_local)),
        ("global", "All my projects", str(dest_global)),
    ]
    cursor = 0
    while True:
        stdscr.erase()
        height, width = stdscr.getmaxyx()
        _addstr(stdscr, 0, 0, "Where should the skills be installed?", curses.A_BOLD)
        _addstr(
            stdscr,
            1,
            0,
            "up/down move   enter confirm   q quit",
            curses.A_DIM,
        )
        for i, (_, label, path) in enumerate(options):
            row = 3 + i * 2
            radio = "(\u2022)" if i == cursor else "( )"
            attr = curses.A_REVERSE if i == cursor else curses.A_NORMAL
            _addstr(
                stdscr,
                row,
                0,
                _clip(f"  {radio} {label}", width - 1),
                attr,
            )
            _addstr(stdscr, row + 1, 0, _clip(f"       {path}", width - 1), curses.A_DIM)
        _addstr(stdscr, height - 1, 0, " " * (width - 1), curses.A_DIM)
        stdscr.refresh()

        key = stdscr.getch()
        if key in (curses.KEY_UP, ord("k")):
            cursor = max(0, cursor - 1)
        elif key in (curses.KEY_DOWN, ord("j")):
            cursor = min(len(options) - 1, cursor + 1)
        elif key in (curses.KEY_ENTER, 10, 13, ord(" ")):
            return options[cursor][0]
        elif key in (ord("q"), 27):
            return None


# --------------------------------------------------------------------------- #
# Plain-text fallbacks
# --------------------------------------------------------------------------- #


def _choose_skills_text(skills: list) -> list | None:
    print("\nAvailable skills:\n")
    for i, skill in enumerate(skills, 1):
        print(f"  {i}) {skill.name}")
        if skill.description:
            print(f"      {skill.description}")
    print()
    try:
        answer = input("Select skills (e.g. 1,3) or 'all' [all]: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return None
    if not answer or answer.lower() == "all":
        return list(skills)
    chosen = []
    for part in answer.replace(" ", "").split(","):
        if not part:
            continue
        if part.isdigit() and 1 <= int(part) <= len(skills):
            chosen.append(skills[int(part) - 1])
        else:
            print(f"  ignoring invalid entry: {part}")
    return chosen or None


def _choose_scope_text(dest_local: Path, dest_global: Path) -> str | None:
    print("\nWhere should the skills be installed?\n")
    print(f"  1) This project      {dest_local}")
    print(f"  2) All my projects   {dest_global}\n")
    try:
        answer = input("Location [1]: ").strip()
    except EOFError:
        print("(no input; defaulting to local)")
        return "local"
    except KeyboardInterrupt:
        print()
        return None
    return "global" if answer == "2" else "local"


# --------------------------------------------------------------------------- #
# Install / uninstall
# --------------------------------------------------------------------------- #


def install_skill(skill: Skill, dest_root: Path, force: bool) -> tuple:
    dest = dest_root / skill.name
    if dest.resolve() == skill.source.resolve():
        return "skip", f"already in place: {dest}"
    if dest.exists():
        if not force:
            return "skip", f"exists (use --force): {dest}"
        shutil.rmtree(dest)
    dest_root.mkdir(parents=True, exist_ok=True)
    shutil.copytree(skill.source, dest, ignore=IGNORE)
    if not (dest / "SKILL.md").is_file():
        return "fail", f"copied but no SKILL.md found in {dest}"
    return "ok", str(dest)


def uninstall_skill(skill: Skill, dest_root: Path) -> tuple:
    dest = dest_root / skill.name
    if not dest.exists():
        return "skip", f"not installed: {dest}"
    shutil.rmtree(dest)
    return "ok", str(dest)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def _print_plan(verb: str, skills: list, dest_root: Path) -> None:
    print(f"\nWill {verb} {len(skills)} skill(s) into:\n  {dest_root}\n")
    for skill in skills:
        print(f"  - {skill.name}")
        print(f"      from {skill.source}")
    print()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Install the skills in this repository.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--list", action="store_true", help="list available skills and exit")
    parser.add_argument("--all", action="store_true", help="install every skill")
    parser.add_argument(
        "--skills",
        metavar="NAMES",
        help="comma-separated skill names (see --list)",
    )
    parser.add_argument(
        "--scope",
        choices=SCOPES,
        help="local = ./.opencode/skills, global = ~/.config/opencode/skills",
    )
    parser.add_argument(
        "--target",
        metavar="DIR",
        help="install into DIR instead of a standard scope location",
    )
    parser.add_argument("--force", action="store_true", help="replace an existing installation")
    parser.add_argument("--uninstall", action="store_true", help="remove instead of install")
    parser.add_argument("--dry-run", action="store_true", help="show what would happen")
    parser.add_argument(
        "--repo",
        metavar="DIR",
        default=str(REPO_ROOT),
        help="repository to read skills from (default: the script's directory)",
    )
    return parser


def _select_skills(args, skills: list):
    by_name = {s.name: s for s in skills}

    if args.all:
        return list(skills)
    if args.skills:
        chosen = []
        for name in (n.strip() for n in args.skills.split(",")):
            if not name:
                continue
            if name not in by_name:
                print(f"error: unknown skill '{name}'. Known: {', '.join(by_name)}", file=sys.stderr)
                return None
            chosen.append(by_name[name])
        return chosen

    if not _can_use_curses():
        return _choose_skills_text(skills)
    try:
        return curses.wrapper(_choose_skills_curses, skills)
    except curses.error:
        return _choose_skills_text(skills)


def main(argv=None) -> int:
    locale.setlocale(locale.LC_ALL, "")
    args = build_parser().parse_args(argv)

    repo = Path(args.repo).expanduser().resolve()
    skills = discover_skills(repo)
    if not skills:
        print(f"error: no skills found under {repo}", file=sys.stderr)
        return 2

    if args.list:
        print(f"Skills in {repo}:\n")
        for skill in skills:
            print(f"  {skill.name}")
            print(f"      {skill.description}")
        return 0

    verb = "uninstall" if args.uninstall else "install"

    selected = _select_skills(args, skills)
    if not selected:
        print("Nothing selected. Aborted.")
        return 1

    dest_local = scope_root("local", None)
    dest_global = scope_root("global", None)

    if args.target:
        scope = "custom"
        dest_root = scope_root("local", args.target)
    elif args.scope:
        scope = args.scope
        dest_root = scope_root(scope, None)
    elif _can_use_curses():
        chosen_scope = curses.wrapper(_choose_scope_curses, dest_local, dest_global)
        if not chosen_scope:
            print("Nothing selected. Aborted.")
            return 1
        scope = chosen_scope
        dest_root = scope_root(scope, None)
    else:
        chosen_scope = _choose_scope_text(dest_local, dest_global)
        if not chosen_scope:
            print("Nothing selected. Aborted.")
            return 1
        scope = chosen_scope
        dest_root = scope_root(scope, None)

    _print_plan(verb, selected, dest_root)
    if args.dry_run:
        print("Dry run: nothing was changed.")
        return 0

    results = {"ok": 0, "skip": 0, "fail": 0}
    for skill in selected:
        if args.uninstall:
            status, message = uninstall_skill(skill, dest_root)
        else:
            status, message = install_skill(skill, dest_root, args.force)
        results[status] += 1
        label = {"ok": "OK  ", "skip": "skip", "fail": "FAIL"}[status]
        print(f"  [{label}] {skill.name}: {message}")

    print(
        f"\nDone ({scope}): {results['ok']} {verb}ed, "
        f"{results['skip']} skipped, {results['fail']} failed."
    )
    if results["fail"]:
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nCancelled.")
        raise SystemExit(130)

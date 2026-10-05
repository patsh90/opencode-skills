#!/usr/bin/env python3
"""Round-trip helper for Anki "Notes in Plain Text" exports (Anki 2.1.55+).

Stdlib only. Commands:

  inspect  EXPORT.txt                    header, column map, counts, lint summary
  to-json  EXPORT.txt CARDS.json         editable JSON (one object per note)
  lint     EXPORT.txt|CARDS.json [--media DIR] [--json]
  build    EXPORT.txt FIXED.json OUTDIR [--all]
                                         writes OUTDIR/corrected.txt (changed notes,
                                         same header, GUIDs kept -> updates in place),
                                         OUTDIR/new_cards.txt (notes with "new": true),
                                         OUTDIR/changes.md (before/after diff)

JSON note object:
  {"row": 3, "guid": "...", "notetype": "Basic", "deck": "Bio", "tags": "a b",
   "fields": ["front", "back"],
   "verdict": "OK|FIX|REWRITE|SPLIT|DELETE?|UNVERIFIED",   # optional, reviewer fills
   "issues": ["..."], "note": "why", "new": false}
Only "fields", "tags" and the review keys may be edited. guid/notetype/deck of
existing rows are taken from the original export; changing a guid is an error.
"""
import csv
import html
import json
import os
import re
import sys
from html.parser import HTMLParser

SEPARATORS = {
    "tab": "\t", "comma": ",", "semicolon": ";", "space": " ",
    "pipe": "|", "colon": ":",
}
SPECIAL_KEYS = {"guid column": "guid", "notetype column": "notetype",
                "deck column": "deck", "tags column": "tags"}


# ---------------------------------------------------------------- reading

def read_export(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        text = f.read()
    lines = text.split("\n")
    header_lines, meta = [], {}
    i = 0
    while i < len(lines) and lines[i].startswith("#") and ":" in lines[i]:
        header_lines.append(lines[i].rstrip("\r"))
        k, v = lines[i][1:].rstrip("\r").split(":", 1)
        meta[k.strip().lower()] = v.strip()
        i += 1
    sep_raw = meta.get("separator", "tab")
    sep = SEPARATORS.get(sep_raw.lower(), sep_raw if len(sep_raw) == 1 else "\t")
    body = "\n".join(lines[i:])
    rows = [r for r in csv.reader(_io(body),
                                  delimiter=sep, quotechar='"') if r != []]
    special = {}  # 0-based index -> role
    for key, role in SPECIAL_KEYS.items():
        if key in meta:
            special[int(meta[key]) - 1] = role
    notes = []
    for n, r in enumerate(rows, start=1):
        note = {"row": n, "guid": "", "notetype": meta.get("notetype", ""),
                "deck": meta.get("deck", ""), "tags": meta.get("tags", ""),
                "fields": []}
        for idx, val in enumerate(r):
            role = special.get(idx)
            if role:
                note[role] = val
            else:
                note["fields"].append(val)
        notes.append(note)
    return {"path": path, "header_lines": header_lines, "meta": meta,
            "sep": sep, "special": special, "notes": notes}


def _io(s):
    import io
    return io.StringIO(s, newline="")


def load_notes(path):
    if path.endswith(".json"):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data["notes"] if isinstance(data, dict) else data
    return read_export(path)["notes"]


# ---------------------------------------------------------------- lint

MATH_RE = re.compile(r"\\\((.*?)\\\)|\\\[(.*?)\\\]", re.S)
DOLLAR_RE = re.compile(r"(?<![\\\[])\$(?!\])([^$\n<]{1,200}?)(?<![\\\[])\$(?!\])")
CLOZE_OPEN = re.compile(r"\{\{c(\d+)::")
YESNO_RE = re.compile(r"^\s*(is|are|was|were|does|do|did|can|could|should|will|would|has|have|had)\b", re.I)
VOID = {"br", "img", "hr", "input", "meta", "link", "source", "wbr", "col", "area", "base", "embed", "param", "track"}


class _TagCounter(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.errors, self.imgs = [], [], []

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            self.imgs.append(dict(attrs).get("src", ""))
        if tag not in VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        if tag == "img":
            self.imgs.append(dict(attrs).get("src", ""))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if tag in self.stack:
            while self.stack and self.stack[-1] != tag:
                self.errors.append(f"unclosed <{self.stack.pop()}>")
            self.stack.pop()
        else:
            self.errors.append(f"stray </{tag}>")


def plain(s):
    return html.unescape(re.sub(r"<[^>]+>", " ", s)).strip()


def cloze_scan(s):
    """Return (numbers, problems). Handles nesting; '}}' closes innermost."""
    nums, probs, depth, i = [], [], 0, 0
    while i < len(s):
        m = CLOZE_OPEN.match(s, i)
        if m:
            nums.append(int(m.group(1)))
            depth += 1
            i = m.end()
            continue
        if s.startswith("}}", i) and depth:
            depth -= 1
            i += 2
            continue
        i += 1
    if depth:
        probs.append(f"{depth} unclosed cloze(s)")
    return nums, probs


def lint_field(text, is_first, is_cloze_type):
    issues = []
    # HTML balance
    tc = _TagCounter()
    try:
        tc.feed(text)
        tc.close()
    except Exception as e:  # pragma: no cover
        issues.append(("warn", f"HTML parse error: {e}"))
    for e in tc.errors:
        issues.append(("warn", f"HTML {e}"))
    for t in tc.stack:
        issues.append(("warn", f"HTML unclosed <{t}>"))
    # math delimiters
    for a, b, name in (("\\(", "\\)", "inline"), ("\\[", "\\]", "display")):
        if text.count(a) != text.count(b):
            issues.append(("error", f"unbalanced MathJax {name} delimiters {a} {b}"))
    has_cloze = "{{c" in text
    for m in MATH_RE.finditer(text):
        body = m.group(1) if m.group(1) is not None else m.group(2)
        b = html.unescape(re.sub(r"<br\s*/?>", "", body))
        b_noesc = b.replace("\\{", "").replace("\\}", "")
        if b_noesc.count("{") != b_noesc.count("}"):
            issues.append(("error", f"unbalanced braces in math: {body[:60]!r}"))
        if b.count("\\left") != b.count("\\right"):
            issues.append(("error", f"\\left/\\right mismatch in math: {body[:60]!r}"))
        if has_cloze and "}}" in body and not CLOZE_OPEN.search(body):
            issues.append(("error", "'}}' inside math in a cloze note closes the cloze early; "
                                    "write '} }' or '}<!-- -->}'"))
        if re.search(r"<(b|i|u|span|div|font)\b", body):
            issues.append(("warn", "HTML formatting tags inside math (editor residue)"))
    for m in DOLLAR_RE.finditer(text):
        inner = m.group(1)
        if re.search(r"[\\^_{}=]", inner):
            issues.append(("warn", f"$...$ math is not rendered by Anki: ${inner[:40]}$ -> use \\( \\)"))
    # cloze
    nums, probs = cloze_scan(text)
    for p in probs:
        issues.append(("error", p))
    if "{{c" in text and not nums:
        issues.append(("error", "malformed cloze (expected {{c1::...}})"))
    # prompt heuristics on first field
    if is_first:
        p = plain(text)
        if not p and not tc.imgs:
            issues.append(("error", "empty first field"))
        if not is_cloze_type and YESNO_RE.match(p) and p.rstrip().endswith("?"):
            issues.append(("style", "possible yes/no question"))
        if len(p) > 300:
            issues.append(("style", f"long prompt ({len(p)} chars) - pattern-matching risk"))
    return issues, nums, tc.imgs


def lint_note(note, media_dir=None):
    fields = note.get("fields", [])
    is_cloze_type = "cloze" in (note.get("notetype") or "").lower() or any("{{c" in f for f in fields)
    out, all_nums, imgs = [], [], []
    for i, f in enumerate(fields):
        issues, nums, im = lint_field(f, i == 0, is_cloze_type)
        all_nums += nums
        imgs += im
        out += [(sev, f"field {i + 1}: {msg}") for sev, msg in issues]
    if "cloze" in (note.get("notetype") or "").lower() and not all_nums:
        out.append(("error", "cloze note type but no cloze deletions"))
    if all_nums:
        u = sorted(set(all_nums))
        if u != list(range(1, u[-1] + 1)):
            out.append(("warn", f"cloze numbers not contiguous {u} (gaps leave empty cards)"))
    if media_dir:
        for src in imgs:
            if src and not src.startswith(("http:", "https:", "data:")) and \
                    not os.path.exists(os.path.join(media_dir, html.unescape(src))):
                out.append(("warn", f"missing media file: {src}"))
    return out


def lint(notes, media_dir=None):
    res = {}
    fronts = {}
    for n in notes:
        iss = lint_note(n, media_dir)
        key = plain(n["fields"][0]).lower() if n.get("fields") else ""
        if key:
            fronts.setdefault(key, []).append(n.get("row"))
        if iss:
            res[n.get("row")] = iss
    for key, rows in fronts.items():
        if len(rows) > 1:
            for r in rows:
                res.setdefault(r, []).append(("warn", f"duplicate first field (rows {rows})"))
    return res


# ---------------------------------------------------------------- writing

def write_rows(path, header_lines, rows, sep):
    with open(path, "w", encoding="utf-8", newline="") as f:
        for h in header_lines:
            f.write(h + "\n")
        w = csv.writer(f, delimiter=sep, quotechar='"', quoting=csv.QUOTE_MINIMAL,
                       lineterminator="\n")
        for r in rows:
            w.writerow(r)


def note_to_row(note, special, width_hint=None):
    fields = list(note["fields"])
    total = len(fields) + len(special)
    row, fi = [], 0
    for idx in range(total):
        role = special.get(idx)
        if role:
            row.append(note.get(role, "") or "")
        else:
            row.append(fields[fi] if fi < len(fields) else "")
            fi += 1
    return row


def build(export_path, fixed_path, outdir, include_all=False):
    exp = read_export(export_path)
    with open(fixed_path, encoding="utf-8") as f:
        data = json.load(f)
    fixed = data["notes"] if isinstance(data, dict) else data
    orig = {n["row"]: n for n in exp["notes"]}
    os.makedirs(outdir, exist_ok=True)
    changed, new, errors, log = [], [], [], []
    for n in fixed:
        if n.get("new"):
            new.append(n)
            continue
        o = orig.get(n.get("row"))
        if o is None:
            errors.append(f"row {n.get('row')}: not in original export (set \"new\": true for new notes)")
            continue
        if n.get("guid", o["guid"]) != o["guid"]:
            errors.append(f"row {o['row']}: GUID changed - refusing (would create a duplicate)")
            continue
        if len(n["fields"]) != len(o["fields"]):
            errors.append(f"row {o['row']}: field count {len(n['fields'])} != original {len(o['fields'])}")
            continue
        merged = dict(o)
        merged["fields"] = n["fields"]
        if "tags" in n:
            merged["tags"] = n["tags"]
        diff = merged["fields"] != o["fields"] or merged["tags"] != o["tags"]
        if diff or include_all:
            changed.append(merged)
            log.append((o, merged, n))
    if errors:
        print("BUILD ERRORS:\n  " + "\n  ".join(errors), file=sys.stderr)
        sys.exit(2)
    if "guid column" not in exp["meta"]:
        print("WARNING: export has no GUID column; Anki will match on the FIRST FIELD. "
              "Notes whose first field you changed will be imported as NEW notes. "
              "Re-export with 'Include unique identifier' ticked.", file=sys.stderr)
    corrected = os.path.join(outdir, "corrected.txt")
    write_rows(corrected, exp["header_lines"],
               [note_to_row(n, exp["special"]) for n in changed], exp["sep"])
    if new:
        nh = ["#separator:tab", "#html:true", "#notetype column:1", "#deck column:2",
              "#tags column:3"]
        rows = [[n.get("notetype", ""), n.get("deck", ""), n.get("tags", "")] + list(n["fields"])
                for n in new]
        write_rows(os.path.join(outdir, "new_cards.txt"), nh, rows, "\t")
    # post-build lint of what will be imported
    post = lint(changed + new)
    with open(os.path.join(outdir, "changes.md"), "w", encoding="utf-8") as f:
        f.write(f"# Changes\n\n{len(changed)} updated notes, {len(new)} new notes.\n\n")
        if post:
            f.write("## Remaining lint findings\n\n")
            for r, iss in post.items():
                for sev, msg in iss:
                    f.write(f"- row {r} [{sev}] {msg}\n")
            f.write("\n")
        for o, m, n in log:
            f.write(f"## Row {o['row']} - {n.get('verdict', 'changed')}\n\n")
            if n.get("issues"):
                f.write("Issues: " + "; ".join(n["issues"]) + "\n\n")
            if n.get("note"):
                f.write(f"Why: {n['note']}\n\n")
            for i, (a, b) in enumerate(zip(o["fields"], m["fields"]), 1):
                if a != b:
                    f.write(f"Field {i}\n\n- before: `{a}`\n- after:  `{b}`\n\n")
            if o["tags"] != m["tags"]:
                f.write(f"Tags: `{o['tags']}` -> `{m['tags']}`\n\n")
        if new:
            f.write("## New notes\n\n")
            for n in new:
                f.write(f"- [{n.get('notetype')}] " + " | ".join(n["fields"]) + "\n")
    print(f"wrote {corrected} ({len(changed)} notes)")
    if new:
        print(f"wrote {os.path.join(outdir, 'new_cards.txt')} ({len(new)} notes)")
    print(f"wrote {os.path.join(outdir, 'changes.md')}")
    if post:
        n_err = sum(1 for v in post.values() for s, _ in v if s == "error")
        print(f"post-build lint: {n_err} errors, see changes.md")
        if n_err:
            sys.exit(3)


# ---------------------------------------------------------------- CLI

def main(argv):
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return
    cmd = argv[1]
    if cmd == "inspect":
        exp = read_export(argv[2])
        print("header:", *exp["header_lines"], sep="\n  ")
        print("separator:", repr(exp["sep"]))
        print("special columns (1-based):", {k + 1: v for k, v in exp["special"].items()})
        if "guid column" not in exp["meta"]:
            print("WARNING: no GUID column - re-export with 'Include unique identifier' "
                  "to update notes in place.")
        if exp["meta"].get("html", "true").lower() != "true":
            print("WARNING: exported without HTML - reimport would strip formatting/images.")
        from collections import Counter
        nt = Counter(n["notetype"] for n in exp["notes"])
        print(f"notes: {len(exp['notes'])}; notetypes: {dict(nt)}")
        print("field counts:", dict(Counter(len(n['fields']) for n in exp['notes'])))
        res = lint(exp["notes"])
        sev = Counter(s for v in res.values() for s, _ in v)
        print(f"lint: {dict(sev)} across {len(res)} notes (run 'lint' for detail)")
    elif cmd == "to-json":
        exp = read_export(argv[2])
        data = {"source": os.path.abspath(argv[2]), "meta": exp["meta"], "notes": exp["notes"]}
        with open(argv[3], "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print(f"wrote {argv[3]} ({len(exp['notes'])} notes)")
    elif cmd == "lint":
        media = argv[argv.index("--media") + 1] if "--media" in argv else None
        res = lint(load_notes(argv[2]), media)
        if "--json" in argv:
            print(json.dumps({str(k): v for k, v in res.items()}, ensure_ascii=False, indent=1))
        else:
            for r, iss in res.items():
                for sev, msg in iss:
                    print(f"row {r}\t[{sev}]\t{msg}")
            print(f"-- {len(res)} notes with findings")
    elif cmd == "build":
        build(argv[2], argv[3], argv[4], include_all="--all" in argv)
    else:
        print(f"unknown command {cmd}\n{__doc__}")
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv)

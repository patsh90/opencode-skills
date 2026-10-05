#!/usr/bin/env python3
"""Convert a Markdown letter (YAML frontmatter + body) to ODT, then verify it.

    python3 md2odt.py path/to/letter.md [--force] [--no-pdf] [--reference X.odt]

Writes <name>.odt and <name>.pdf next to the source .md, and preview PNGs of
pages 1-2 in a temp folder. Exit codes:
    0  files written, all checks passed
    1  files written, but a check FAILED or could not run (read the report)
    2  error (missing tool, pandoc/LibreOffice failure, bad input)
    3  <name>.odt or <name>.pdf already exists and --force was not given;
       nothing was written. Ask the user before re-running with --force.

Standard library only. Needs pandoc; LibreOffice (soffice) and poppler-utils
(pdftoppm, pdffonts, pdfinfo, pdftotext) are needed for the verification.
"""
import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.dom import minidom

SKILL_DIR = Path(__file__).resolve().parent.parent
A4 = (210.0, 297.0)          # A4 only (EU); there is no other paper size
DEFAULTS = {"margins": "25mm", "font": "Liberation Serif", "font_size": "12pt",
            "line_spacing": "1.15", "align": "left", "language": "pl-PL"}

report = {"assumptions": [], "checks": [], "problems": []}


def ok(msg): report["checks"].append("OK    " + msg)
def fail(msg): report["problems"].append(msg); report["checks"].append("FAIL  " + msg)
def warn(msg): report["problems"].append(msg); report["checks"].append("WARN  " + msg)
def assume(msg): report["assumptions"].append(msg)


def die(msg, code=2):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(code)


def run(cmd, timeout=180, check=True):
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if check and p.returncode != 0:
        die(f"command failed ({p.returncode}): {' '.join(cmd)}\n{p.stderr.strip()}")
    return p


# ------------------------------------------------------------ metadata
def stringify(node):
    """Plain text of a pandoc JSON Meta*/Inline/Block node."""
    if isinstance(node, list):
        return "".join(stringify(n) for n in node)
    if not isinstance(node, dict):
        return str(node)
    t, c = node.get("t"), node.get("c")
    if t in ("Str", "MetaString"):
        return c
    if t == "Space":
        return " "
    if t in ("SoftBreak", "LineBreak"):
        return "\n"
    if t == "MetaBool":
        return "true" if c else "false"
    if t == "MetaList":
        return "\n".join(stringify(x) for x in c)
    if t in ("Code", "Math"):
        return c[-1]
    if t in ("Link", "Image", "Span", "Quoted", "Cite"):
        return stringify(c[1] if t != "Cite" else c[1])
    if t in ("Para", "Plain"):
        return stringify(c) + "\n"
    if t == "MetaMap":
        return ""
    return stringify(c) if c is not None else ""


def read_meta(src):
    p = run(["pandoc", str(src), "-f", "markdown", "-t", "json"])
    meta = json.loads(p.stdout).get("meta", {})
    out = {}
    for k, v in meta.items():
        if v.get("t") == "MetaBool":
            out[k] = v["c"]
        else:
            out[k] = stringify(v).strip()
    return out


def length_mm(value):
    m = re.fullmatch(r"\s*([\d.]+)\s*(mm|cm|in|pt)?\s*", str(value))
    if not m:
        die(f"cannot read length {value!r} (use e.g. 25mm, 2.5cm, 1in)")
    n, unit = float(m.group(1)), m.group(2) or "mm"
    return n * {"mm": 1, "cm": 10, "in": 25.4, "pt": 25.4 / 72}[unit]


# ------------------------------------------------- template overrides
def patch_reference(ref, out, meta):
    """Copy reference.odt to `out`, applying frontmatter layout overrides."""
    with zipfile.ZipFile(ref) as z:
        files = {i.filename: z.read(i.filename) for i in z.infolist()}
    doc = minidom.parseString(files["styles.xml"])

    def styles_named(name, family=None):
        for el in doc.getElementsByTagName("style:style"):
            if el.getAttribute("style:name") == name and (
                    family is None or el.getAttribute("style:family") == family):
                yield el

    def child(el, tag):
        found = el.getElementsByTagName(tag)
        if found:
            return found[0]
        new = doc.createElement(tag)
        el.appendChild(new)
        return new

    w, h = A4
    margin = length_mm(meta["margins"])
    for pl in doc.getElementsByTagName("style:page-layout"):
        props = child(pl, "style:page-layout-properties")
        props.setAttribute("fo:page-width", f"{w}mm")
        props.setAttribute("fo:page-height", f"{h}mm")
        for side in ("top", "left", "right"):
            props.setAttribute(f"fo:margin-{side}", f"{margin:.2f}mm")
        has_footer = any(fs.getElementsByTagName("style:header-footer-properties")
                         for fs in pl.getElementsByTagName("style:footer-style"))
        # Footer (5 mm gap + 10 mm box) sits inside the bottom margin on pages 2+.
        bottom = max(margin - 15, 5) if has_footer else margin
        props.setAttribute("fo:margin-bottom", f"{bottom:.2f}mm")

    default = [d for d in doc.getElementsByTagName("style:default-style")
               if d.getAttribute("style:family") == "paragraph"][0]
    tp = child(default, "style:text-properties")
    font = meta["font"]
    tp.setAttribute("style:font-name", font)
    tp.setAttribute("fo:font-size", meta["font_size"] if re.search(r"[a-z]", meta["font_size"])
                    else meta["font_size"] + "pt")
    lang = meta["language"]
    parts = re.split(r"[-_]", lang)
    tp.setAttribute("fo:language", parts[0].lower())
    if len(parts) > 1:
        tp.setAttribute("fo:country", parts[1].upper())
    elif tp.hasAttribute("fo:country"):
        tp.removeAttribute("fo:country")

    decls = doc.getElementsByTagName("office:font-face-decls")[0]
    if not any(f.getAttribute("style:name") == font for f in decls.getElementsByTagName("style:font-face")):
        ff = doc.createElement("style:font-face")
        ff.setAttribute("style:name", font)
        ff.setAttribute("svg:font-family", f"'{font}'")
        ff.setAttribute("style:font-pitch", "variable")
        decls.appendChild(ff)

    try:
        spacing = float(meta["line_spacing"])
    except ValueError:
        die(f"line_spacing must be a number like 1.15, got {meta['line_spacing']!r}")
    align = meta["align"].lower()
    if align not in ("left", "justify", "justified"):
        die(f"align must be left or justify, got {meta['align']!r}")
    for body in styles_named("Text_20_body", "paragraph"):
        pp = child(body, "style:paragraph-properties")
        pp.setAttribute("fo:line-height", f"{round(spacing * 100)}%")
        pp.setAttribute("fo:text-align", "justify" if align.startswith("justif") else "start")
        child(body, "style:text-properties").setAttribute(
            "fo:hyphenate", "true" if align.startswith("justif") else "false")

    files["styles.xml"] = doc.toxml(encoding="UTF-8")
    with zipfile.ZipFile(out, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), files.pop("mimetype"), compress_type=zipfile.ZIP_STORED)
        for name, data in files.items():
            z.writestr(name, data, compress_type=zipfile.ZIP_DEFLATED)


# ---------------------------------------------------------- verification
def frame_info(odt):
    """Geometry (mm) and text lines of the address frames in content.xml."""
    content = minidom.parseString(zipfile.ZipFile(odt).read("content.xml"))
    frames = {}
    for f in content.getElementsByTagName("draw:frame"):
        g = {k: length_mm(f.getAttribute("svg:" + k).replace("mm", ""))
             for k in ("x", "y", "width", "height")}
        g["lines"] = ["".join(n.data for n in p.childNodes if n.nodeType == n.TEXT_NODE)
                      for p in f.getElementsByTagName("text:p")]
        frames[f.getAttribute("draw:name")] = g
    return frames


def page_words(pdf, page):
    p = run(["pdftotext", "-f", str(page), "-l", str(page), "-bbox", str(pdf), "-"], check=False)
    words = []
    for m in re.finditer(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>', p.stdout):
        x0, y0, x1, y1 = (float(m.group(i)) * 25.4 / 72 for i in range(1, 5))
        words.append((x0, y0, x1, y1, m.group(5).replace("&amp;", "&").replace("&lt;", "<")
                      .replace("&gt;", ">").replace("&quot;", '"').replace("&apos;", "'")))
    return words


def page_text(pdf, page):
    return run(["pdftotext", "-f", str(page), "-l", str(page), "-layout", str(pdf), "-"], check=False).stdout


def inside(word, g, tol=0.8):
    x0, y0, x1, y1, _ = word
    return (x0 >= g["x"] - tol and x1 <= g["x"] + g["width"] + tol and
            y0 >= g["y"] - tol and y1 <= g["y"] + g["height"] + tol)


def verify(odt, pdf, meta, preview_dir):
    info = run(["pdfinfo", str(pdf)]).stdout
    pages = int(re.search(r"Pages:\s+(\d+)", info).group(1))
    pw, ph = (float(x) * 25.4 / 72 for x in re.search(r"Page size:\s+([\d.]+) x ([\d.]+)", info).groups())
    ew, eh = A4
    (ok if abs(pw - ew) < 1 and abs(ph - eh) < 1 else fail)(
        f"paper A4: PDF page is {pw:.1f} x {ph:.1f} mm, {pages} page(s)")

    # fonts: requested font installed, used, and every font embedded
    fc = run(["fc-match", "-f", "%{family}", meta["font"]], check=False).stdout if shutil.which("fc-match") else ""
    if fc and meta["font"].lower() not in fc.lower():
        fail(f"font '{meta['font']}' is not installed here; fontconfig substitutes '{fc}'")
    fonts = run(["pdffonts", str(pdf)]).stdout.splitlines()[2:]
    names, not_emb = set(), []
    for line in fonts:
        cols = line.split()
        if len(cols) < 5:
            continue
        name = cols[0].split("+", 1)[-1]
        names.add(name)
        emb = cols[-5] if len(cols) >= 7 else "?"
        if emb != "yes":
            not_emb.append(name)
    wanted = meta["font"].replace(" ", "").lower()
    others = sorted(n for n in names if not n.replace("-", "").lower().startswith(wanted))
    if any(n.replace("-", "").lower().startswith(wanted) for n in names):
        ok(f"font '{meta['font']}' used in PDF" + (f" (also: {', '.join(others)})" if others else ""))
    else:
        fail(f"font '{meta['font']}' not found in PDF; fonts used: {', '.join(sorted(names)) or 'none'}")
    (fail if not_emb else ok)("all PDF fonts embedded" if not not_emb else
                              f"fonts NOT embedded: {', '.join(not_emb)}")

    # window envelope: every recipient word inside the window, nothing else intrudes
    frames = frame_info(odt)
    words1 = page_words(pdf, 1)
    if "Recipient" in frames:
        g = frames["Recipient"]
        allowed = set(" ".join(g["lines"]).split())
        missing = [w for w in allowed if not any(ww[4] == w and inside(ww, g) for ww in words1)]
        if missing:
            fail(f"recipient text outside the envelope window or missing: {' '.join(missing[:8])} "
                 f"(window {g['x']:.1f}/{g['y']:.1f} mm, {g['width']:.0f} x {g['height']:.1f} mm; "
                 f"{len(g['lines'])} lines)")
        else:
            ok(f"recipient ({len(g['lines'])} lines) inside window at x={g['x']:.1f} y={g['y']:.1f} mm, "
               f"{g['width']:.0f} x {g['height']:.1f} mm")
        # sender block and return line must render too (LibreOffice silently
        # drops or moves frames that overlap each other)
        for name in ("Sender", "ReturnLine", "Date"):
            fg = frames.get(name)
            if not fg or not "".join(fg["lines"]).strip():
                continue
            lost = [w for w in " ".join(fg["lines"]).split()
                    if not any(ww[4] == w and inside(ww, fg) for ww in words1)]
            (fail if lost else ok)(f"{name} block rendered in place" if not lost else
                                   f"{name} block missing or displaced: {' '.join(lost[:8])}")
        ret = set(" ".join(frames.get("ReturnLine", {}).get("lines", [])).split())
        intruders = [ww[4] for ww in words1 if inside(ww, g, tol=-0.5) and ww[4] not in allowed | ret]
        (fail if intruders else ok)("no other text inside the window area" if not intruders else
                                    f"other text overlaps the window: {' '.join(intruders[:8])}")

    # page numbers: none on page 1, "2 / N" on page 2
    t1 = page_text(pdf, 1)
    if pages > 1:
        t2 = page_text(pdf, 2)
        has2 = re.search(rf"\b2\s*/\s*{pages}\b", t2) is not None
        no1 = re.search(rf"\b1\s*/\s*{pages}\b", t1) is None
        (ok if has2 and no1 else fail)(
            "page numbers from page 2 onward" if has2 and no1 else
            f"page numbering wrong (page 1 numbered: {not no1}, page 2 shows '2 / {pages}': {has2})")
    else:
        ok("single page, no page number shown") if not re.search(r"\b1\s*/\s*1\b", t1) else fail("page number on a 1-page letter")

    # closing and signature on the same page; last page not just the sign-off
    closing, sig = meta.get("closing", ""), meta.get("signature_name", "")
    if closing and sig and pages > 1:
        texts = [page_text(pdf, i) for i in range(1, pages + 1)]
        flat = [" ".join(t.split()) for t in texts]
        pc = max((i for i, t in enumerate(flat) if " ".join(closing.split()) in t), default=None)
        ps = max((i for i, t in enumerate(flat) if " ".join(sig.split()) in t), default=None)
        (ok if pc == ps else fail)("closing and signature on the same page" if pc == ps else
                                   f"closing (page {pc and pc + 1}) and signature (page {ps and ps + 1}) are split")
        last = " ".join(texts[-1].split())
        for s in (closing, sig, meta.get("signature_title", ""), meta.get("enclosures", ""),
                  f"{pages}/{pages}", f"{pages} / {pages}"):
            for part in s.split("\n"):
                last = last.replace(" ".join(part.split()), "")
        if len(last.split()) <= 3:
            warn("the last page holds only the sign-off; consider tightening the body")

    # previews for visual inspection
    run(["pdftoppm", "-r", "100", "-png", "-f", "1", "-l", str(min(pages, 2)), str(pdf),
         str(preview_dir / "page")], check=False)
    return sorted(preview_dir.glob("page*.png")), pages


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", type=Path)
    ap.add_argument("--force", action="store_true", help="overwrite existing .odt/.pdf (only after the user agreed)")
    ap.add_argument("--no-pdf", action="store_true", help="do not keep the PDF next to the source (still verified)")
    ap.add_argument("--reference", type=Path, default=SKILL_DIR / "reference.odt")
    ap.add_argument("--filter", type=Path, default=SKILL_DIR / "letter.lua")
    args = ap.parse_args()

    src = args.input.resolve()
    if not src.is_file():
        die(f"input not found: {src}")
    out_odt, out_pdf = src.with_suffix(".odt"), src.with_suffix(".pdf")

    # 1. toolchain
    tools = {t: shutil.which(t) for t in ("pandoc", "soffice", "libreoffice", "pdftoppm",
                                         "pdffonts", "pdfinfo", "pdftotext", "fc-match")}
    if not tools["pandoc"]:
        die("pandoc is not installed; install it (e.g. apt install pandoc / brew install pandoc)")
    soffice = tools["soffice"] or tools["libreoffice"]
    pandoc_v = run(["pandoc", "--version"]).stdout.splitlines()[0]

    # 2. never overwrite without permission
    existing = [p for p in (out_odt, out_pdf) if p.exists() and not (p == out_pdf and args.no_pdf)]
    if existing and not args.force:
        print("EXISTS: " + ", ".join(str(p) for p in existing))
        print("Nothing written. Ask the user whether to overwrite, then re-run with --force "
              "(or rename/move the source).")
        sys.exit(3)

    # 3. metadata, defaults, assumptions
    raw = read_meta(src)
    meta = dict(DEFAULTS)
    meta.update({k: str(v) if not isinstance(v, bool) else v for k, v in raw.items()})
    if str(raw.get("paper", "a4")).lower() != "a4":
        die(f"this skill is A4-only (EU); got paper: {raw['paper']!r}. Remove the key or set it to a4")
    meta["language"] = raw.get("language") or raw.get("lang") or DEFAULTS["language"]
    for key, allowed in (("window_side", ("left", "right")), ("date_position", ("top", "below")),
                         ("signature_side", ("left", "right"))):
        if key in raw and str(raw[key]).lower() not in allowed:
            die(f"{key} must be one of {', '.join(allowed)}, got {raw[key]!r}")
    for k in ("margins", "font", "font_size", "line_spacing", "align", "language"):
        if k not in raw and not (k == "language" and "lang" in raw):
            assume(f"{k}: {DEFAULTS[k]} (default)")
    is_letter = raw.get("layout", "letter" if raw.get("recipient") else "document") == "letter"
    if is_letter:
        # same defaults as letter.lua: Polish convention for Polish, DIN 5008 otherwise
        polish = re.split(r"[-_]", meta["language"])[0].lower() == "pl"
        side = str(raw.get("window_side", "right" if polish else "left")).lower()
        date_pos = str(raw.get("date_position", "top" if polish and side == "right" else "below")).lower()
        if side == "left" and date_pos == "top":
            date_pos = "below"
            warn("date_position: top needs window_side: right (the top-right column is the sender's); "
                 "date placed below the address")
        sig_side = str(raw.get("signature_side", "right" if polish else "left")).lower()
        conv = "Polish convention" if polish else "DIN 5008"
        for key, val in (("window_side", side), ("date_position", date_pos), ("signature_side", sig_side)):
            if key not in raw:
                assume(f"{key}: {val} ({conv} default)")
        if not raw.get("date"):
            assume(f"date: none given, used today ({dt.date.today().isoformat()})")
        if not raw.get("sender"):
            warn("no sender given: no sender block or return line")
        if not raw.get("subject"):
            warn("no subject line given")
        if not raw.get("salutation"):
            assume("salutation: none in frontmatter, expected as first line of the body")
        if not raw.get("closing"):
            warn("no closing given (e.g. 'Yours faithfully,')")
        if not raw.get("signature_name") and raw.get("sender"):
            meta["signature_name"] = raw["sender"].split("\n")[0]
            assume(f"signature_name: used first sender line '{meta['signature_name']}'")
    else:
        assume("layout: document (no recipient given): no address blocks")

    # 4. template with overrides, then pandoc
    tmp = Path(tempfile.mkdtemp(prefix="md2odt-"))
    ref = tmp / "reference.odt"
    patch_reference(args.reference, ref, meta)
    tmp_odt = tmp / out_odt.name
    cmd = ["pandoc", str(src), "--from", "markdown", "--to", "odt",
           "--reference-doc", str(ref), "--lua-filter", str(args.filter), "-o", str(tmp_odt)]
    run(cmd)

    # 5. PDF via LibreOffice headless (isolated profile, so a running LibreOffice doesn't block it)
    previews, pages, tmp_pdf = [], None, tmp / out_pdf.name
    if soffice:
        p = run([soffice, f"-env:UserInstallation=file://{tmp}/lo-profile", "--headless",
                 "--convert-to", "pdf", "--outdir", str(tmp), str(tmp_odt)], timeout=240, check=False)
        if not tmp_pdf.exists():
            fail(f"LibreOffice PDF export failed: {p.stderr.strip() or p.stdout.strip()}")
    else:
        fail("LibreOffice (soffice) not installed: layout NOT verified, no PDF preview")

    if tmp_pdf.exists():
        missing = [t for t in ("pdftoppm", "pdffonts", "pdfinfo", "pdftotext") if not tools[t]]
        if missing:
            fail(f"poppler-utils missing ({', '.join(missing)}): checks and preview skipped")
        else:
            previews, pages = verify(tmp_odt, tmp_pdf, meta, tmp)

    # 6. deliver
    shutil.copyfile(tmp_odt, out_odt)
    written = [out_odt]
    if tmp_pdf.exists() and not args.no_pdf:
        shutil.copyfile(tmp_pdf, out_pdf)
        written.append(out_pdf)

    print("== md2odt report ==")
    print(f"pandoc:    {pandoc_v}")
    print(f"soffice:   {soffice or 'not installed'}")
    print(f"template:  {args.reference}  (patched copy: {ref})")
    print(f"command:   {' '.join(cmd)}")
    print("written:   " + ", ".join(str(p) for p in written) + (f"  ({pages} page(s))" if pages else ""))
    print("previews:  " + (", ".join(str(p) for p in previews) or "none"))
    print("assumptions:")
    for a in report["assumptions"] or ["none"]:
        print("  - " + a)
    print("checks:")
    for c in report["checks"]:
        print("  " + c)
    print("RESULT: " + ("PROBLEMS FOUND, see FAIL/WARN above" if report["problems"] else "all checks passed"))
    sys.exit(1 if report["problems"] else 0)


if __name__ == "__main__":
    main()

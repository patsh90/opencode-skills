---
name: markdown-to-odt-letters
description: Convert Markdown files with YAML frontmatter into print-ready A4 OpenDocument Text (.odt) for formal documents the user will print and mail, primarily Polish letters and pisma (wnioski, wypowiedzenia, odwołania, umowy) and other EU letters, with window-envelope address placement, a styled reference.odt template and PDF-based layout verification. Load when the user asks to turn a .md into an .odt, or wants a printable or mailable letter in ODT/LibreOffice format. Not for .docx output or PDF-only requests.
compatibility: opencode
metadata:
  tested-with: "pandoc 3.1.3, LibreOffice 24.2, poppler-utils 24"
---

# Markdown → ODT for printed letters (Polish first, A4/EU)

Turns `something.md` (YAML frontmatter + Markdown body) into `something.odt`
and a `something.pdf` preview, laid out as a formal letter for a window
envelope, or as a plain formal document when there is no recipient.

- **Polish is the default language and layout.** Letters are assumed to be
  Polish (`pl-PL`) unless the frontmatter says otherwise. Other EU languages
  work and get the German DIN 5008 layout.
- **A4 paper only.** There is no US Letter mode.
- All styling lives in `reference.odt`. The Lua filter only decides which
  named style each part uses and where the address frames go. Never fix
  layout with per-document hacks: change the template instead (see "Changing
  the look").

`SKILL_DIR` below means the folder containing this file, for example
`~/.config/opencode/skills/markdown-to-odt-letters` or
`.opencode/skills/markdown-to-odt-letters`.

## When to use / when not to use

Use for:
- a `.md` file that should become an `.odt` to print, sign and post: pisma,
  wnioski, wypowiedzenia, reklamacje, odwołania, podania, simple umowy, and
  their equivalents in other EU languages;
- a request for a letter as an ODT or LibreOffice document.

Do **not** use for:
- **.docx / Word output.** Use a docx workflow; this template is ODT-only.
- **PDF-only requests** ("just give me a PDF"). The PDF here is a preview byproduct.
- **US Letter paper or US-style letters** (#10 envelopes, "September 28,
  2026" dates). The wrapper stops with an error on `paper: letter`.
- Anything needing a letterhead logo, multiple columns, fillable forms (e.g.
  official ZUS/US forms), mail merge, or exact reproduction of a third-party
  template. Say so rather than bending this skill.
- Court filings (pisma procesowe) that must follow a specific court's formal
  requirements: this skill lays out a letter, it does not check legal form.
- Long reports or books (TOC, cross-references, bibliography). Use a normal
  pandoc/LaTeX workflow.

## Files in this skill

| File | Purpose |
|---|---|
| `reference.odt` | Style template: page styles (A4, 25 mm margins, no number on page 1, `n / N` footer from page 2), fonts, body/heading/address/date/signature paragraph styles, address frame style |
| `letter.lua` | pandoc filter: builds sender block, return line, recipient window, place and date, reference, subject, salutation, closing, signature, numbered enclosures from the frontmatter |
| `scripts/md2odt.py` | Wrapper: toolchain check, overwrite guard, frontmatter overrides → patched template copy, pandoc, LibreOffice PDF, automated checks, report |
| `scripts/make_reference.py` | Regenerates `reference.odt` from code (reproducible template) |
| `examples/letter.md` | Polish example with every frontmatter field (the default case) |
| `examples/letter-en.md` | English example (DIN 5008 layout) |

## Step 1: Check the toolchain

```sh
pandoc --version | head -1                              # required
command -v soffice || command -v libreoffice            # required for verification
command -v pdftoppm pdffonts pdfinfo pdftotext          # poppler-utils, for checks/preview
command -v fc-match                                     # font availability check
fc-list :lang=pl family | grep -i "liberation serif"    # default font covers Polish diacritics
python3 -c "import odf" 2>/dev/null && echo "odfpy present (not needed)"
```

Decide:
- **pandoc present** → use this skill's pipeline (always the preferred path).
- **pandoc missing** → stop and ask the user to install it (`apt install pandoc`,
  `brew install pandoc`, `winget install pandoc`). Do not hand-build the ODT
  with odfpy or raw XML: the styling would drift from the template and nothing
  would be verified. odfpy is not used by this skill.
- **LibreOffice or poppler missing** → you can still convert, but the report
  will say "NOT verified". Tell the user plainly. Never claim the layout is
  correct without the PDF check.
- LibreOffice is used **only** for PDF export and verification, never for the
  conversion itself.

## Step 2: Check the input

The source is Markdown with YAML frontmatter. The frontmatter **keys stay in
English**, but the values are in the letter's language. Read the file before
converting and point out missing essentials (recipient, subject, closing)
instead of inventing them.

| Key | Required | Notes |
|---|---|---|
| `sender` | letter: yes | list of lines, or a `\|` block. First line = name. Printed top left (Polish) / top right (DIN), and as the return line |
| `recipient` | letter: yes | list of lines or `\|` block. Its presence selects letter layout. Max ~6 lines at 12 pt |
| `place` | recommended (pl) | "Warszawa" → "Warszawa, 28 września 2026 r." |
| `date` | no | `YYYY-MM-DD` is written out in the letter's language: pl "28 września 2026 r." (genitive month + "r."), de "28. September 2026", fr "1er octobre 2026". Other text (e.g. "28.09.2026 r.") is used verbatim. Missing → today (reported as an assumption) |
| `subject` | recommended | bold subject line, e.g. "Wniosek o …" / "Wypowiedzenie umowy …". Add "Dotyczy: " yourself if wanted |
| `reference` | no | printed as "Znak sprawy: …" (other languages: "Reference:", "Aktenzeichen:"…; override the label with `reference_label`, e.g. "Sygn. akt:") |
| `language` | no | BCP 47. Default **`pl-PL`**. Sets hyphenation/spell-check language, date format, labels and the layout defaults below. Localized dates and labels: pl, en, de, fr, es, it, nl, pt, cs, fi, sv, da |
| `salutation` | no | e.g. "Szanowni Państwo," / "Szanowna Pani," / "Szanowny Panie Dyrektorze,". If absent, the body's first line is taken to be the salutation |
| `closing` | yes | e.g. "Z poważaniem" / "Z wyrazami szacunku" (Polish: no comma) |
| `signature_name` | yes | typed name under ~3 lines of signing space. Missing → first sender line (reported) |
| `signature_title` | no | line(s) under the name, e.g. "Pełnomocnik", "Prezes Zarządu" |
| `enclosures` | no | list, printed numbered under "Załączniki:" (other languages localized; override with `enclosures_label`) |
| `title`, `subtitle` | document layout | for notices and contracts without a recipient |

Body: plain Markdown: paragraphs, `**bold**`, `*italic*`, bullet and numbered
lists, simple pipe tables, and `#` headings for contracts ("§ 1", "Uzasadnienie").
Avoid images, raw HTML and footnote-heavy text. They convert, but they are
outside what this skill verifies.

## Step 3: Layout defaults (overridable in frontmatter)

Layout choices follow the letter's language: **Polish convention** for `pl`,
**DIN 5008** for every other language.

| Key | Polish default | Other languages | Allowed |
|---|---|---|---|
| `window_side` | `right` (okienko prawe) | `left` | `left`, `right`. Check the user's envelopes |
| `date_position` | `top` (top right, above the window) | `below` (under the address, right-aligned) | `top` (needs `window_side: right`), `below` |
| `signature_side` | `right` (closing + signature centred in the right half) | `left` | `left`, `right` |
| `margins` | `25mm` | same | any length: `20mm`, `2.5cm` (top/left/right; bottom kept equivalent on pages 2+ with the footer) |
| `font` | `Liberation Serif` | same | any installed family with Polish glyphs; `Carlito` / `Liberation Sans` for a clean sans |
| `font_size` | `12pt` | same | 11–12 pt recommended |
| `line_spacing` | `1.15` | same | number |
| `align` | `left` | same | `left`, `justify` (turns on hyphenation; needs LibreOffice's Polish hyphenation dictionary, `hyphen-pl`) |
| `return_line` | on | same | `true`, `false`, or custom text. Built from the postal sender lines only; phone/e-mail/web lines are left out |
| `fold_marks` | `false` | same | `true`: fold marks at 105 / 210 mm plus punch mark at 148.5 mm |
| `window_left`, `window_top`, `window_width`, `window_height` | see below | same | lengths, to match a specific envelope |
| `layout` | `letter` if `recipient` set, else `document` | same | `letter`, `document` |

Fixed by the template (change `reference.odt` to alter them):
- Paper: A4 portrait only (210 × 297 mm).
- **Polish letter order:** sender (top left) | place and date (top right) →
  return line + recipient in the right-hand window → znak sprawy → subject
  (bold) → salutation → body → closing, ~15 mm (~3 lines) signing space,
  name/title in the right half → numbered "Załączniki:" at the left.
- **DIN 5008 order (other languages):** sender (top right) → return line +
  recipient in the left-hand window → date (right-aligned, below the address)
  → reference → subject → salutation → body → closing, signing space, name
  (left) → enclosures.
- Window position: the DIN 5008 form B / ISO 269 address field for DL, C5
  and C6 window envelopes (window 90 × 45 mm, 20 mm from the side edge, 15 mm
  from the bottom). The return line is at 57 mm and the address at 62.7–90 mm
  from the top. It starts 25 mm from the left edge (`left`), or 105 mm from
  the left edge, ending at the right margin (`right`). Polish shops sell both
  "okienko prawe" and "okienko lewe" envelopes, so tell the user to
  test-fold one printout.
- Headings keep with the next paragraph, and body text has 2-line widow and
  orphan control. Address blocks are frames and cannot break across pages.
  Closing, signature, title and enclosures are kept together as one block.
- Page 1 uses the "First Page" style with no page number. Pages 2+ show
  `n / N` centred in the footer.

## Step 4: Convert (exact commands)

Standard path, which does everything in Steps 4 and 5:

```sh
python3 "$SKILL_DIR/scripts/md2odt.py" path/to/pismo.md
```

Options: `--force` overwrites an existing `.odt`/`.pdf` (only after the user
said yes). `--no-pdf` still verifies but doesn't keep the PDF.
`--reference X.odt` uses another template.

Exit codes: `0` all checks passed · `1` files written but a check FAILED or
WARNed · `2` error · `3` output exists, nothing written.

For transparency, this is what the wrapper runs. Run directly, pandoc uses
the template defaults, and the filter still applies the Polish layout
defaults. The frontmatter overrides of font, size, margins, spacing,
alignment and language (in the template) are applied only by the wrapper,
which patches a temporary copy of the template:

```sh
# 1. ODT (styles from the template, letter structure from the filter)
pandoc pismo.md --from markdown --to odt \
  --reference-doc "$SKILL_DIR/reference.odt" \
  --lua-filter "$SKILL_DIR/letter.lua" \
  -o pismo.odt

# 2. PDF preview via LibreOffice headless (isolated profile, so a running
#    LibreOffice instance does not block the conversion)
soffice -env:UserInstallation=file:///tmp/lo-md2odt --headless \
  --convert-to pdf --outdir . pismo.odt

# 3. Render page 1 (and 2) for visual inspection
pdftoppm -r 100 -png -f 1 -l 2 pismo.pdf /tmp/pismo-page

# 4. Font check
fc-match -f '%{family}\n' "Liberation Serif"   # must return the same family
pdffonts pismo.pdf                              # every row: emb = yes
```

## Step 5: Verify (mandatory; report problems, don't claim success)

1. **Read the `md2odt` report.** Each `FAIL`/`WARN` line is a real problem to
   pass on to the user. The `assumptions:` section lists every default that
   was applied (language, window side, date position…). Automated checks:
   - the page is A4;
   - the requested font is installed (`fc-match`) and actually used in the
     PDF, and every PDF font is embedded;
   - every recipient word lies inside the envelope window, and no other text
     overlaps the window;
   - the sender block, return line and top date rendered where they should
     (LibreOffice silently moves overlapping frames, and a too-long return
     line wraps into the address);
   - no page number on page 1, and `2 / N` on page 2;
   - closing and signature on the same page, and the last page isn't just the
     sign-off.
2. **Look at the preview PNG(s)** listed under `previews:` with your
   image-viewing tool. For a Polish letter, check the sender is top left,
   "Miejscowość, data r." is top right, and the small return line and address
   are in the right-hand window zone. Check the subject is bold, the table
   columns don't collide, and "Z poważaniem" and the name are in the right half
   with room to sign. Check Polish letters (ą ć ę ł ń ó ś ź ż) render and
   nothing is clipped. If you cannot view images, say so and give the user the
   PDF path to check themselves. Don't describe a layout you haven't seen.
3. **Fonts and printing.** The PDF embeds its fonts, so printing the PDF
   matches the preview exactly. The ODT does not embed fonts. If the user
   prints the ODT on another machine, the font must be installed there. The
   default Liberation fonts normally ship with LibreOffice and most Linux
   distributions, and cover Polish. If the check reports a substituted font,
   say so and either install the font, pick an installed one
   (`fc-list :lang=pl family`), or recommend printing the PDF.
4. If a check fails, fix the **input** (shorten the address, move text,
   adjust frontmatter overrides) or the **template**, re-run, and report
   what changed. Do not post-edit the generated ODT by hand.

## Step 6: Output rules

- Outputs go **next to the source**: `pismo.md` → `pismo.odt` + `pismo.pdf`.
- **Never overwrite** an existing `.odt` (or `.pdf`) without asking. The
  wrapper exits with code 3 and writes nothing. Ask the user, then re-run with
  `--force`, or suggest another filename.
- Finish with a short summary, in the user's language (Polish if they write
  in Polish):

```
Utworzono: /ścieżka/pismo.odt, /ścieżka/pismo.pdf (1 strona)
Szablon: <SKILL_DIR>/reference.odt (A4, Liberation Serif 12 pt, wyrównanie do lewej)
Założenia: brak daty → 2026-09-28; język pl-PL; okienko prawe; data u góry; podpis po prawej
Kontrole: wszystkie zaliczone (albo: każdy FAIL/WARN i co zrobić)
Przed wysłaniem: złóż jeden wydruk do koperty z okienkiem; podpisz nad imieniem i nazwiskiem.
```

## Changing the look

- **Interactively:** open `reference.odt` in LibreOffice and edit styles
  (F11), then save as ODT. The wrapper only overwrites page size/margins,
  default font/size/language, and Text Body spacing/alignment, so every other
  edit is kept. Styles:
  - letter parts: "Letter Sender", "Letter Sender Left", "Letter Return
    Line", "Letter Recipient", "Letter Date" (below the address), "Letter Date
    Top" (top right), "Letter Address Gap", "Letter Reference", "Letter
    Subject", "Letter Salutation", "Letter Enclosures";
  - sign-off: "Letter Closing", "Letter Signature" and "Letter Signature
    Title", plus their "… Right" variants for the right-half sign-off;
  - body: "Text Body" and "First Paragraph"; headings "Heading 1–4";
  - page styles: "First Page" and "Default Page Style".
- **Reproducibly:** edit `scripts/make_reference.py` and run it to regenerate
  `reference.odt`.
- **Window geometry** lives in the `GEOMETRY` table in `letter.lua` (`left`
  and `right`). Per-letter overrides go in the frontmatter (`window_top`, …).
- **Centred title** for a formal pismo (e.g. "WNIOSEK"): set "Letter Subject"
  to centred in the template. Per-letter centring isn't supported.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `this skill is A4-only (EU)` error | Remove `paper:` from the frontmatter; US Letter is not supported |
| `recipient text outside the envelope window` | Too many address lines or font too large: shorten, or use `font_size: 11pt` |
| `ReturnLine block missing or displaced` | The return line is too long for the window: shorten the sender lines, or set `return_line: "Imię Nazwisko · ul. … · 00-000 Miasto"` |
| Date printed below the address although Polish | `window_side: left` was set, so the top-right column holds the sender. Use `window_side: right`, or accept the DIN placement |
| `font … not installed; fontconfig substitutes …` | Install the font or choose one from `fc-list :lang=pl family` |
| Justified text has big gaps | The Polish hyphenation dictionary is missing in LibreOffice (`hyphen-pl` package / LibreOffice language pack), or use `align: left` |
| LibreOffice conversion hangs/fails | Another instance is locked: the wrapper already uses an isolated profile; kill stray `soffice.bin` and retry |
| Table columns squeezed | The filter sizes columns by content. For long cell text, set explicit widths with dash lengths in a pipe table wider than 72 characters |
| `the last page holds only the sign-off` | Tighten the body or drop a paragraph; closing, signature and enclosures are deliberately kept together |

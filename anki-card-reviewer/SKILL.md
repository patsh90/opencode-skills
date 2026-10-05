---
name: anki-card-reviewer
description: Review and fix Anki flashcards exported as "Notes in Plain Text" (.txt/.tsv) - find factual, cloze, HTML and MathJax errors, rewrite weak prompts using evidence-based card-writing rules, add visuals only when asked, and produce a file that reimports into Anki updating notes in place.
license: MIT
compatibility: opencode
metadata:
  input: Anki "Notes in Plain Text" export (Anki 2.1.55+)
  output: corrected.txt, new_cards.txt, changes.md
---

# Anki card reviewer

You audit and rewrite the user's exported Anki notes and hand back a file Anki
can import to update those notes in place, keeping review history. Accuracy
beats preserving the user's wording, but a card that is already good stays as it is.

All helper commands use `scripts/anki_tsv.py` in this skill's directory
(Python 3 stdlib only). Below, `$S` means the path to that script, e.g.
`~/.config/opencode/skills/anki-card-reviewer/scripts/anki_tsv.py`.

Read `references/card-rules.md` before reviewing. Read
`references/anki-format.md` if the export looks unusual or the user asks how to
export or import.

## Workflow

1. **Check the export.**
   `python3 $S inspect EXPORT.txt`
   - No GUID column: stop and tell the user to re-export with
     *Include unique identifier* ticked. Without it, Anki matches on the first
     field, so any edited front becomes a duplicate note.
   - `#html:false`: tell the user to re-export with *Include HTML and media
     references*, or formatting and images will be lost on reimport.
2. **Convert to JSON.**
   `python3 $S to-json EXPORT.txt cards.json`, then
   `python3 $S lint cards.json` (add `--media <collection.media path>` if the user
   gives it). The linter finds mechanical problems only: cloze/MathJax/HTML
   syntax, `$…$` math, likely yes/no fronts, duplicates, cloze-number gaps. It
   does not judge facts or prompt quality. That part is your job.
3. **Review in batches** of about 25–40 notes. Copy `cards.json` to `fixed.json`
   and edit only `fields` and `tags`; add `verdict`, `issues`, `note` to each
   note you touch. For each note:
   1. **Correctness.** Is the fact true, current, and not overstated? If it's
      wrong, fix it and say why in `note`. If you can't verify it, use verdict
      `UNVERIFIED` and leave the content unchanged. Never add plausible-sounding
      facts that aren't in the card or a source you checked.
   2. **Mechanics.** Typos, cloze syntax, MathJax, HTML residue.
   3. **Prompt quality.** Apply `references/card-rules.md`.
   4. **Verdict:** `OK` (untouched), `FIX` (small correction), `REWRITE`,
      `SPLIT`, `DELETE?` (never delete, only flag), or `UNVERIFIED`.
   - **Split:** rewrite the original note as the first part (it keeps its GUID
     and history), then add each extra part as a new object:
     `{"new": true, "notetype": "...", "deck": "...", "tags": "...", "fields": [...]}`
     with the same field count as that note type.
   - Keep the field count, note type and GUID of every existing note unchanged.
     A note that needs a different note type (e.g. Basic → Cloze) goes in as
     `new`, with the original marked `DELETE?`.
   - Tag every note you change by adding `reviewed::fixed`, `reviewed::rewritten` or
     `reviewed::split`, and add `reviewed::delete-candidate` / `reviewed::unverified`
     where those apply. These tags let the user find the notes in the browser afterwards.
     Only do this if the export has a tags column.
4. **Build the import files.**
   `python3 $S build EXPORT.txt fixed.json OUTDIR`
   - `corrected.txt`: changed notes only, original header, GUIDs kept.
   - `new_cards.txt`: notes from splits or note-type changes.
   - `changes.md`: before/after of every change plus any remaining lint findings.
   It exits non-zero on changed GUIDs, field-count mismatches or lint errors in
   the output. Fix those and rebuild.
5. **Report to the user:** counts per verdict, recurring problems across the
   deck, every `UNVERIFIED` / `DELETE?` item, and the import steps below.

## Reimport steps to give the user

1. Back up first: *File → Export → Anki Collection Package*, or rely on Anki's
   automatic backups.
2. *File → Import* `corrected.txt`. Check the header was detected (note type, deck
   and GUID taken from the file) and set **Existing notes: Update**. Updated
   notes keep their scheduling.
3. Import `new_cards.txt` the same way. These notes have no GUID, so they are
   added as new.
4. In the Browser, search `tag:reviewed::delete-candidate` and decide which to
   delete. For heavily rewritten cards, you can search `tag:reviewed::rewritten`
   and use *Cards → Reset/Forget* if the old interval no longer fits the new
   question.
5. If cloze numbers were removed or renumbered, run *Tools → Empty Cards* to
   clear the leftover blank cards.

## Math

Use MathJax: `\( … \)` inline, `\[ … \]` display, `\ce{…}` for chemistry. Never
use `$…$`, which Anki does not render. Only keep `[$]…[/$]` / `[latex]` if the
deck already uses Anki's LaTeX-image mode. Inside a cloze, `}}` in the math
ends the cloze early. Put a space between the braces (`x^{2} }`) or separate
them with `<!-- -->`. Full rules are in `references/card-rules.md`.

## Visuals (only when the user asks)

Don't add images unprompted. When asked, create an original diagram (SVG, or
PNG from matplotlib/graphviz), save it next to the output with a unique, simple
filename, reference it as `<img src="name.png">` in the field, and tell the user
to copy the file into their `collection.media` folder before importing. Follow
the visual rules in `references/card-rules.md`. For labelling diagrams, suggest
Anki's built-in Image Occlusion; it can't be created through text import.

## Don'ts

- Don't renumber or restructure cards that are fine. Every change resets the
  user's familiarity with the prompt.
- Don't make the answer longer to seem thorough. One card, one answer.
- Don't touch GUID, note type or deck columns.
- Don't state a verdict you haven't checked.

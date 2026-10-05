# opencode-skills

A small collection of [OpenCode](https://opencode.ai) skills. Each skill teaches the
agent a repeatable workflow it would not otherwise follow — planning code changes
before writing them, producing a print-ready letter, or auditing a flashcard deck.

- [What is a skill?](#what-is-a-skill)
- [Install](#install)
- [Skills](#skills)
  - [project-steward](#project-steward) — plan and trace every code change
  - [markdown-to-odt-letters](#markdown-to-odt-letters) — Markdown → printable A4 letter (ODT/PDF)
  - [anki-card-reviewer](#anki-card-reviewer) — audit and fix exported Anki notes
- [Repository layout](#repository-layout)
- [License](#license)

## What is a skill?

A skill is a folder containing a `SKILL.md` file with a short YAML frontmatter (a
`name` and a `description`) and instructions the agent follows when the skill is
loaded. OpenCode shows the model only the name and description; the body is read when
the model decides the skill applies, or when you ask for it by name. That is why each
description here is written to say clearly *when* the skill should be used.

## Install

Skills live in one of two places, and the folder name must match the `name` in
`SKILL.md`:

| Scope | Path | Use when |
| --- | --- | --- |
| Local | `./.opencode/skills/<skill-name>/` | One project — commit it so the whole team gets it |
| Global | `~/.config/opencode/skills/<skill-name>/` | All your projects |

### Interactive installer (recommended)

`install.py` copies the skills for you. It has no dependencies beyond Python 3
(standard library only) and is run from the repository root:

```sh
python3 install.py
```

It works in two steps. First a checkbox picker, then a choice of location:

```text
Select skills to install
up/down move   space toggle   a all   n none   enter install   q quit

  ▸[x] anki-card-reviewer
       Review and fix Anki flashcards exported as …
    [ ] markdown-to-odt-letters
       Convert Markdown files with YAML frontmatter into …
    [ ] project-steward
       Keeps a software project planned and traceable …

 1 selected

Where should the skills be installed?
up/down move   enter confirm   q quit

  ▸(•) This project       /you/my-project/.opencode/skills
   ( ) All my projects    /home/you/.config/opencode/skills
```

- **Local** installs into the project you run the script from (`./.opencode/skills`).
  Commit it so the whole team gets the skills.
- **Global** installs into `~/.config/opencode/skills` (or `$XDG_CONFIG_HOME`).
- The picker is built by scanning the repository for `SKILL.md` files, so a new skill
  directory appears automatically — no list to maintain.
- A skill that is already installed is skipped. Pass `--force` to replace it.

**Non-interactive flags** (skip the picker):

| Flag | Meaning |
| --- | --- |
| `--list` | print the available skills and exit |
| `--all` | select every skill |
| `--skills NAME,NAME` | only these skills (by the `name` in `SKILL.md`) |
| `--scope local\|global` | where to install |
| `--target DIR` | a custom directory instead of a standard scope |
| `--force` | replace an existing installation |
| `--uninstall` | remove the selected skills instead of installing |
| `--dry-run` | print the plan and change nothing |

```sh
python3 install.py --list                                   # show available skills
python3 install.py --all --scope global                     # every skill, globally
python3 install.py --skills project-steward,anki-card-reviewer
python3 install.py --skills markdown-to-odt-letters --scope local
python3 install.py --all --target ./vendor/skills           # any custom directory
python3 install.py --all --force                            # replace existing installs
python3 install.py --all --uninstall --scope global         # remove
python3 install.py --all --dry-run                          # show what would happen
```

In a shell with no terminal it falls back to a numbered prompt, and if no `--scope`
is given it installs **locally**.

### Manually

Copy a skill folder into place, keeping its folder name:

```sh
mkdir -p ~/.config/opencode/skills
cp -r anki-card-reviewer        ~/.config/opencode/skills/
cp -r markdown-to-odt-letters   ~/.config/opencode/skills/
cp -r project-steward-skill/project-steward ~/.config/opencode/skills/
# Then ask the agent to use a skill by name, or describe a task that matches
# its description.
```

## Skills

### project-steward

**Context.** A new agent session starts with no memory of the last one, and the
project's plan survives only if it is written down. Left alone, an agent will happily
write code that contradicts a decision made last week, or build scope the user never
agreed to.

**What it does.** Enforces a plan-first, ticket-driven workflow in **any programming
language**. Before any change beyond a typo, formatting or a comment, the agent:

1. reads `ARCHITECTURE.md` and `MILESTONES.md` and the open tickets;
2. checks the request against the project's non-goals and current milestone, and
   stops to ask if it conflicts;
3. updates the documents (with a decision-log entry) if the plan or architecture
   changes;
4. drafts a ticket in `tickets/` from `TICKET_TEMPLATE.md` before writing code;
5. implements **one ticket at a time** on a `ticket/NNNN-slug` branch, using
   test-driven development where it helps (with the reason written in the ticket);
6. closes the ticket with evidence for each acceptance criterion and a full test run.

On first use in a project it reads whatever code exists, interviews you (purpose,
what the project should make obsolete, features, non-goals, constraints), then writes
`ARCHITECTURE.md`, `MILESTONES.md`, `tickets/TICKET_TEMPLATE.md` and a rule in
`AGENTS.md`, and drafts tickets for the first milestone.

> **Install note.** The skill lives in `project-steward-skill/project-steward/`. The
> folder you copy must stay named `project-steward`, not `project-steward-skill`.

**Example usage.**

```text
You:   Load the project-steward skill and set up this project.
Agent: [reads the code, interviews you, writes ARCHITECTURE.md,
        MILESTONES.md and tickets/, adds an AGENTS.md rule]

You:   Add a "forgot password" flow.
Agent: [reads the plan, checks non-goals — it fits the current milestone,
        drafts ticket 0007 and waits for approval because ARCHITECTURE.md changed]
       Drafted T-0007: password reset via e-mail.
       Approve and I'll implement it on ticket/0007-password-reset.
```

Because the rule is in `AGENTS.md` (always in context), later sessions load the skill
before touching code on their own. It is still an instruction, not a hard lock — the
user can always say "skip the process".

Files it manages in your project: `ARCHITECTURE.md`, `MILESTONES.md`,
`tickets/NNNN-slug.md`. Behaviour is editable in `project-steward/SKILL.md`,
`references/first-run.md` and `templates/`.

### markdown-to-odt-letters

**Context.** You have a formal letter written in Markdown and need a print-ready A4
document to sign and mail — for example a Polish *pismo* (wniosek, wypowiedzenie,
odwołanie) that will go into a window envelope. Getting the address block to line up
with the envelope window by hand is fiddly and easy to get wrong.

**What it does.** Turns a Markdown file with YAML frontmatter into an `.odt` plus a
PDF preview, laid out for a window envelope (or as a plain formal document when there
is no recipient). Polish is the default language and layout; other EU languages get
the German **DIN 5008** layout. It is A4-only.

It then **verifies** the result: the page is A4, the requested fonts are installed and
embedded, every word of the recipient address lies inside the envelope window, the
sender/date/return line rendered where they should, page numbering is right, and the
sign-off is not orphaned. Outputs are written next to the source and an existing
`.odt` is never overwritten without asking.

**Requirements.** `pandoc` is required. LibreOffice (`soffice`) and `poppler-utils`
are required for the PDF verification step; without them the conversion still runs
but is reported as **not verified**.

**Example usage.** Write `pismo.md` with frontmatter (see
`markdown-to-odt-letters/examples/letter.md` for the Polish default and
`letter-en.md` for English):

```yaml
---
sender:
  - Anna Przykładowa
  - ul. Przykładowa 12/4
  - 00-950 Warszawa
recipient:
  - Przykładowa Spółdzielnia Mieszkaniowa
  - ul. Wzorcowa 5
  - 30-001 Kraków
place: Warszawa
date: 2026-09-28
subject: Wypowiedzenie umowy najmu lokalu mieszkalnego nr 4
language: pl-PL
salutation: Szanowni Państwo,
closing: Z poważaniem
signature_name: Anna Przykładowa
enclosures:
  - Kopia umowy najmu
---
Niniejszym wypowiadam umowę najmu lokalu mieszkalnego nr 4 …
```

Then either ask the agent, or run the wrapper directly:

```sh
python3 scripts/md2odt.py pismo.md
# → pismo.odt + pismo.pdf, with a report of all layout checks
```

Exit codes: `0` all checks passed, `1` files written but a check failed or warned,
`2` error, `3` output exists and nothing was written (re-run with `--force`). Use
`--no-pdf` to verify without keeping the PDF, or `--reference X.odt` for another
template.

**Not for:** `.docx`/Word output, PDF-only requests, US Letter paper, letterhead
logos, fillable forms, mail merge, or court filings that must follow a specific
court's formal requirements.

### anki-card-reviewer

**Context.** A flashcard deck accumulates weak cards: facts that are slightly wrong,
yes/no prompts, unreadable MathJax, and cards that are memorized by their wording
rather than by the answer. The hard part of fixing them is not editing text — it is
reimporting without losing review history or the notes' GUIDs.

**What it does.** Audits an Anki export and hands back a file Anki can import to
update notes **in place**, keeping scheduling. It:

1. **checks the export** — without a GUID column any edited front becomes a
   duplicate; without HTML, formatting and images are lost on reimport;
2. **converts and lints** — finds mechanical problems (cloze/MathJax/HTML syntax,
   `$…$` math that Anki does not render, likely yes/no fronts, duplicates, cloze
   numbering gaps);
3. **reviews in batches** for *correctness* (flagging `UNVERIFIED` rather than
   inventing facts), *mechanics*, and *prompt quality* against evidence-based
   card-writing rules — using verdicts `OK`, `FIX`, `REWRITE`, `SPLIT`, `DELETE?`,
   `UNVERIFIED`;
4. **builds the import files** — `corrected.txt` (changed notes, GUIDs kept),
   `new_cards.txt` (splits and note-type changes), and `changes.md` (before/after of
   every change);
5. **reports** counts per verdict, recurring problems, and any `UNVERIFIED` or
   `DELETE?` items, with step-by-step reimport instructions.

It never deletes a note, never changes a GUID, note type or deck, and never adds
images unless you ask.

**Requirements.** Python 3 (standard library only). Export from Anki 2.1.55+ as
*Notes in Plain Text (.txt)* with **Include unique identifier (GUID)**, **Include
HTML and media references**, **Include tags** and **Include notetype name** ticked.

**Example usage.** In Anki: Browser → *Notes → Export Notes* → "Notes in Plain Text"
with all the boxes ticked, and save as `export.txt`. Then ask the agent to review
`export.txt`, or drive the helper script yourself:

```sh
S=~/.config/opencode/skills/anki-card-reviewer/scripts/anki_tsv.py
python3 "$S" inspect export.txt          # verifies GUID + HTML columns
python3 "$S" to-json export.txt cards.json
python3 "$S" lint cards.json             # mechanical problems only
# … the agent edits fixed.json (fields and tags only) …
python3 "$S" build export.txt fixed.json out/
# → out/corrected.txt, out/new_cards.txt, out/changes.md
```

Reimport in Anki: back up first, then *File → Import* `corrected.txt`, check the
header was detected and set **Existing notes: Update** (updated notes keep their
scheduling). Import `new_cards.txt` the same way. Search
`tag:reviewed::delete-candidate` to decide what to delete, and run *Tools → Empty
Cards* if cloze numbers changed.

## Repository layout

```text
opencode-skills/
├── anki-card-reviewer/            # skill: SKILL.md + references/ + scripts/
├── markdown-to-odt-letters/       # skill: SKILL.md + letter.lua + reference.odt
│                                  #        + scripts/ + examples/
├── project-steward-skill/         # wrapper folder
│   └── project-steward/           # the actual skill: SKILL.md + references/ + templates/
├── install.py                     # interactive installer (stdlib only)
├── LICENSE
└── README.md
```

## License

MIT — see [LICENSE](LICENSE).

# project-steward: an OpenCode skill

Makes the agent plan before it codes, in any programming language. Before any change
beyond a typo, the agent reads `ARCHITECTURE.md` and `MILESTONES.md`, checks the
request against the project's non-goals, updates the documents if the plan changes,
and drafts tickets in `tickets/` from `TICKET_TEMPLATE.md`. Tickets use test-driven
development where it helps, with the reason written in the ticket.

## Install

Copy the `project-steward` folder into one of these locations. The folder name must
stay `project-steward`.

| Scope | Path |
| --- | --- |
| One project (commit it, so the whole team gets it) | `.opencode/skills/project-steward/` |
| All your projects | `~/.config/opencode/skills/project-steward/` |

The same files work on OpenCode v1 and v2.

## First use

In the project, tell the agent: **"Load the project-steward skill and set up this
project."**

It will read whatever code exists, interview you (what the project is for, what it
should make obsolete, features, non-goals, constraints), and then write:

- `ARCHITECTURE.md` and `MILESTONES.md` at the repository root
- `tickets/TICKET_TEMPLATE.md`
- a short rule in `AGENTS.md`
- draft tickets for the first milestone, after you approve the plan

## Why the AGENTS.md rule matters

OpenCode loads a skill only when the model decides to. The model sees the skill's
name and description, not its contents. `AGENTS.md` is always in context, so the rule
there is what makes later sessions load the skill before touching code. Setup adds it
for you; the text is in `project-steward/templates/AGENTS_RULE.md` if you want to add
it by hand.

This is still an instruction, not a lock. A model can ignore it. Blocking edits
outright when no ticket is in progress would need an OpenCode plugin, which this
package does not include.

## What the agent does on each piece of work

1. Reads `ARCHITECTURE.md`, `MILESTONES.md` and the open tickets.
2. Skips the process for questions and for trivial edits (typos, formatting,
   comments).
3. Checks the request against non-goals and the current milestone. On a conflict it
   stops and asks: park it, schedule it later, change the plan, or drop it.
4. Updates the documents if the plan or the architecture changes, with a decision
   log entry (what was decided, why, what was rejected).
5. Drafts tickets from the template.
6. Waits for your approval only if the documents changed. Otherwise it proceeds.
7. Implements one ticket at a time on a `ticket/NNNN-slug` branch, with commits that
   start with `T-NNNN:`. It does not push or merge unless asked.
8. Closes the ticket with evidence for each acceptance criterion and a full test run.

## Changing the behaviour

Everything is plain Markdown.

- Workflow rules, TDD guidance, git conventions: `project-steward/SKILL.md`
- Interview questions: `project-steward/references/first-run.md`
- Document and ticket layouts: `project-steward/templates/`

After setup, each project has its own copy of the ticket template in `tickets/`, so
you can change it per project without touching the skill.

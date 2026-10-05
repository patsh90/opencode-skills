---
name: project-steward
description: Keeps a software project planned and traceable, in any programming language. Load this BEFORE making any change to a codebase beyond a typo, formatting or comment fix (new features, bug fixes, refactors, dependency changes), and whenever the user starts a new project, asks what to build next, or talks about scope, roadmap, milestones, architecture or tickets. It makes the agent read and update ARCHITECTURE.md and MILESTONES.md, check the request against the project's non-goals, and draft tickets in tickets/ from TICKET_TEMPLATE.md before any code is written, using test-driven development where it helps. On first use in a project it interviews the user (features, what the app should make obsolete, constraints) to create those files.
compatibility: opencode
metadata:
  version: "1.0"
---

# Project steward

A session starts with no memory of the last one. The project's plan survives only in
files, so this skill keeps three of them current and makes every change traceable to
a ticket. The order matters: plan first, ticket second, code third. Code written
before the plan is updated is how a project drifts away from what the user wanted.

Nothing here depends on a programming language. The stack, and the exact commands to
build and test, are recorded in `ARCHITECTURE.md` and read from there.

## The files

| File | Holds | Changes when |
| --- | --- | --- |
| `ARCHITECTURE.md` | Purpose, what the project replaces, non-goals, constraints, components, data, build/test commands, decision log | The shape of the system or a recorded decision changes |
| `MILESTONES.md` | Ordered milestones, each with a goal, exit criteria and its tickets; a parking lot for deferred ideas | Scope, order or exit criteria change; a ticket is added or closed |
| `tickets/TICKET_TEMPLATE.md` | The form every ticket is copied from | Rarely, and only when the user asks |
| `tickets/NNNN-short-slug.md` | One unit of work with one verifiable outcome | Throughout the ticket's life |

All paths are relative to the repository root. Files named in this skill under
`templates/` and `references/` are relative to this skill's own directory.

## Before changing anything

Work through these steps in order for each new piece of work.

### 1. Check that the project is set up

If `ARCHITECTURE.md`, `MILESTONES.md` or `tickets/TICKET_TEMPLATE.md` is missing, this
is a first run. Read `references/first-run.md` and follow it. Do not write code until
it is finished.

### 2. Read the plan

Read `ARCHITECTURE.md` and `MILESTONES.md` in full, and the header of every ticket
whose status is not `done` or `dropped`. They are short. Do this at the start of each
new piece of work, not once per session, because the previous ticket may have changed
them.

### 3. Decide what kind of request this is

- **No change to the repository** (a question, an explanation, a review): answer it.
  This skill does not apply.
- **Trivial**: a typo, formatting, a comment. Nothing about behaviour, structure or
  dependencies changes. Just do it; no ticket.
- **Covered by an open ticket**: go to step 7 with that ticket.
- **Anything else**: features, bug fixes, refactors, dependency changes, build or
  deployment changes. Continue to step 4.

If you are unsure whether something is trivial, it is not.

### 4. Check the request against the plan

Compare the request with the Non-goals and Decision log in `ARCHITECTURE.md` and with
the current milestone in `MILESTONES.md`. There are three outcomes.

- **It fits the current milestone.** Continue.
- **It belongs to a later milestone, or to none.** Stop and say so.
- **It contradicts a non-goal or a recorded decision.** Stop and say so, quoting the
  line it contradicts.

When you stop, give the user the choices: put it in the parking lot, schedule it in a
later milestone, change the plan and do it now, or drop it. Wait for the answer. The
user may well choose to change the plan, and that is fine; the point is that the plan
changes on purpose and in writing, not by accident.

A bug in behaviour that already shipped always fits. It needs a ticket but not a
milestone decision.

### 5. Update the documents

Update `ARCHITECTURE.md` when the work adds or removes a component, moves a
responsibility between components, changes stored data or an external interface, adds
or replaces a dependency, or changes a build, test or run command. Record the reason
in the decision log (format below).

Update `MILESTONES.md` when the work adds, removes or reorders scope, or changes an
exit criterion.

If neither applies, leave both as they are. Listing a new ticket under a milestone
that already covers the work is bookkeeping, not a plan change.

If the documents disagree with the code as it stands, say so before going further. Fix
the document when the code is what the user intended, and raise a ticket when the
document is.

### 6. Draft the tickets

For each unit of work, copy `tickets/TICKET_TEMPLATE.md` to
`tickets/NNNN-short-slug.md`, where `NNNN` is the highest existing number plus one,
zero-padded to four digits. Fill in every section. An empty section means the ticket
is not understood yet.

- One ticket has one outcome that can be verified. If the title needs "and", split it.
- Acceptance criteria are observable: a command and its expected result, a behaviour a
  person can see. "Works correctly" is not a criterion.
- Record dependencies on other tickets.
- Decide whether to use test-driven development and write the reason in the ticket
  (see "Choosing test-driven development").
- Set the status to `draft` and add the ticket under its milestone in `MILESTONES.md`.

### 7. Decide whether to wait for the user

Stop and wait for approval if step 5 changed the content of either document. Show
what changed in each document and list the drafted tickets with one line each. If the
user already chose "change the plan" in step 4 and the edits are exactly what they
chose, that was the approval; do not ask twice.

Otherwise tell the user in one or two lines which tickets you drafted, set them to
`ready`, and continue.

### 8. Implement one ticket at a time

Set the ticket to `in-progress`. Keep only one ticket in progress, so the working
tree always corresponds to one ticket. Follow the ticket's approach, and the git
conventions below.

If you discover work the ticket does not cover, draft a new ticket for it. Do not
widen the ticket you are in.

### 9. Close the ticket

- Check each acceptance criterion and write what you ran and what you saw in the
  ticket's log.
- Run the project's full test command from `ARCHITECTURE.md`, not only the new tests.
- Set the status to `done` and tick the ticket in `MILESTONES.md`.
- If the implementation departed from the ticket's approach or from the architecture,
  update `ARCHITECTURE.md` and add a decision log entry.
- If every exit criterion of the milestone is now met, tell the user and ask before
  starting the next milestone. Draft tickets for one milestone at a time; tickets
  drafted far ahead go stale.

## Choosing test-driven development

Use TDD when writing the test first makes the work easier or safer, and skip it when
it does not. Either way, write the choice and the reason in the ticket.

TDD usually helps when:

- the behaviour can be stated as inputs and expected outputs;
- the work is a bug fix (a failing test that reproduces the bug comes first, so the
  fix is proven and the bug cannot return unnoticed);
- the logic has edge cases that are easy to list and easy to forget;
- the work is a refactor of code without tests (write tests that pin down current
  behaviour first, then change the code).

TDD usually does not help when:

- the work is a spike whose purpose is to find out what to build;
- the change is configuration, wiring or generated code with no logic of its own;
- the result is judged by eye (layout, copy, visual design);
- no test harness exists and building one would cost more than the ticket. In that
  case say so, and consider a separate ticket to add the harness.

When you skip TDD, the ticket's test plan must still say how the result will be
verified.

When you use TDD, work in this cycle. Take the test command from `ARCHITECTURE.md`;
do not assume a framework.

1. Write one test for the next small piece of behaviour.
2. Run it and watch it fail. Check that it fails for the expected reason. A test that
   fails because of a typo or a missing import has proven nothing yet.
3. Write the least code that makes it pass.
4. Run the tests and watch them pass.
5. Tidy the code while the tests stay green.
6. Repeat until the acceptance criteria are covered.

Do not weaken or delete a test to make it pass. If a test turns out to be wrong, say
why in the ticket's log and correct it.

## Git conventions

These apply when the repository uses git. If `ARCHITECTURE.md` or `AGENTS.md` records
different conventions for this project, those win.

- Branch per ticket: `ticket/NNNN-short-slug`, created from the main branch.
- Commit messages start with the ticket ID: `T-0007: reject expired tokens`.
- Changes to `ARCHITECTURE.md`, `MILESTONES.md` and the ticket file go in the same
  branch as the code they describe, so the plan and the code never disagree on any
  commit.
- Do not push, merge or delete branches unless the user asks.

## Decision log

Decisions live at the end of `ARCHITECTURE.md`, newest last. Do not edit or delete an
old entry. When a decision is reversed, add a new entry that names the one it
replaces.

```markdown
### D-012 (2026-03-04): Store sessions in the database, not in memory
- Ticket: T-0031
- Decision: what was chosen, in one or two sentences.
- Why: the constraint or evidence that settled it.
- Rejected: each alternative considered, and why it lost.
- Replaces: D-005 (only when this reverses an earlier decision)
```

A decision belongs in the log if a future session could reasonably undo it without
knowing why it was made.

## When the user tells you to skip the process

The user owns the project. If they say to make a change without a ticket, make it.
Say once that the documents may now be out of date, and offer to write a ticket after
the fact so the record stays complete.

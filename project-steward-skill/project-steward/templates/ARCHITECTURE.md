# Architecture: <project name>

<!-- Keep this file short enough to read in full at the start of every piece of
     work. Describe the system as it is. Remove these comments when filling it in. -->

## Purpose

<!-- One paragraph: what it is, who uses it, what problem it solves. -->

## Replaces

<!-- What this project makes obsolete, and the bar it has to clear. -->

- **Replaces:** <tool, process or older version>
- **Must match:** <what the old thing gets right>
- **Must beat:** <what the old thing gets wrong>
- **Old thing can be dropped when:** <observable condition>

## Non-goals

<!-- What the project will deliberately not do. Requests are checked against this
     list before any ticket is drafted. -->

- <non-goal>

## Constraints

<!-- Platform, language, hosting, budget, deadlines, performance, privacy, licences. -->

- <constraint>

## System overview

<!-- The components, what each is responsible for, and how they talk to each other.
     A short list or a small diagram in text. -->

| Component | Responsibility | Talks to |
| --- | --- | --- |
| <name> | <what it owns> | <other components, and how> |

## Data

<!-- What is stored, where, in what form, and which component owns it. -->

## External dependencies

<!-- Services, libraries and APIs the project relies on, and why each is there. -->

| Dependency | Used for | Notes |
| --- | --- | --- |
| <name> | <purpose> | <version limits, licence, alternatives> |

## Build, test, run

<!-- Exact commands. This section is what lets the workflow stay independent of the
     programming language. Mark any command that has not been confirmed to work. -->

| Task | Command |
| --- | --- |
| Install dependencies | `<command>` |
| Build | `<command>` |
| Run all tests | `<command>` |
| Run one test | `<command>` |
| Lint / format | `<command>` |
| Run locally | `<command>` |

## Conventions

<!-- Only what differs from the defaults: directory layout rules, naming, git
     conventions if they differ from ticket/NNNN-slug branches and T-NNNN commits. -->

## Open questions

<!-- Things not yet decided. Move each to the decision log when it is settled. -->

- <question>

## Decision log

<!-- Newest last. Never edit or delete an old entry; reverse it with a new one. -->

### D-001 (<YYYY-MM-DD>): <decision in a few words>
- Ticket: <T-NNNN, or "setup">
- Decision: <what was chosen>
- Why: <the constraint or evidence that settled it>
- Rejected: <alternatives considered, and why each lost>

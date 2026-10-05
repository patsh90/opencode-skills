# First run: setting up a project

This runs once per project, when `ARCHITECTURE.md`, `MILESTONES.md` or
`tickets/TICKET_TEMPLATE.md` is missing. The result is those three files, a rule in
`AGENTS.md`, and draft tickets for the first milestone. No code is written during
setup.

If only some of the files are missing, keep the ones that exist, read them, and ask
only about what they leave open.

## 1. Look before asking

Find out what is already there, so the user is not asked what the repository can
answer.

- **Empty or near-empty repository**: go straight to the interview.
- **Existing code**: read the README, the dependency manifests, the directory layout,
  the tests and any CI configuration. From these, work out the language and stack,
  the components, and the build, test and run commands. Run the test command once to
  see whether it works. Then interview the user only about what code cannot tell you:
  purpose, what the project replaces, non-goals, and where it goes next.

## 2. Interview the user

The goal is to know enough to write one paragraph on what the project is for, a list
of what it will not do, and a first milestone with exit criteria. Stop when you can
write those. Unanswered details go under Open questions in `ARCHITECTURE.md`; they do
not need to be settled today.

How to ask:

- Ask three to five questions at a time, in rounds. Use a question tool if one is
  available, plain text if not. Three rounds is usually enough.
- Skip anything the user or the repository has already answered.
- Each round should build on the last. Use what you just heard to ask something
  sharper, not the next item on a list.
- This is a brainstorm, not a form. Propose things: features the user has not
  mentioned but that their goal implies, a smaller first version, a risk they have
  not named. Say when two of their answers pull against each other.
- Do not choose a language or framework for the user without saying so. If they have
  no preference, propose one with the reason and let them accept or change it.

### Round 1: purpose and what it replaces

- What is it, in a sentence or two, and who uses it?
- What should it make obsolete? This may be another tool, a spreadsheet, a manual
  routine, or an older version of the same thing.
- What does that existing thing get right, so the new project must match it? What
  does it get wrong, so the new project must beat it?
- What would have to be true for the user to stop using the old thing entirely?

The answers on what it replaces matter most. They set the bar for "done": the
project is not finished when its features exist, it is finished when the old thing is
no longer needed.

### Round 2: features and limits

- Which features are needed before it is useful at all? Which come later?
- What will it deliberately not do? Push for at least two or three non-goals. A
  project with no non-goals has no scope.
- What is the smallest version that could replace the old thing for one real use?
- Where does it run, and for how many users: one person's machine, a server, phones,
  a browser?

### Round 3: constraints and risks

- Language, framework or platform: required, preferred, or open?
- What data does it handle, where does that data come from, and where must it be
  kept? Is any of it private or regulated?
- What must it integrate with?
- Are there hard limits: deadline, budget, offline use, performance, licences?
- Who works on it, and how do they use git today?
- What is the user least sure about? Which part might turn out not to work?

Ask further rounds only for gaps that would change the first milestone.

## 3. Shape the milestones

- Each milestone ends with something a person can use or see, stated as an outcome,
  not as a list of tasks.
- Each milestone names which part of the old thing it makes unnecessary. The last
  milestone is the one after which the old thing can be dropped completely.
- Put the riskiest assumption in the first milestone. If the part the user is least
  sure about fails, it should fail early and cheaply.
- Exit criteria are checkable: a command and its result, or a behaviour someone can
  observe.
- Three to five milestones is typical. Describe the first in detail and later ones
  briefly; they will change.
- Ideas that came up but were not scheduled go in the parking lot, so they are
  neither lost nor silently in scope.

## 4. Write the files

Copy from this skill's `templates/` directory and fill them in.

1. `templates/ARCHITECTURE.md` to `ARCHITECTURE.md`. For existing code, describe the
   system as it is, not as it should be. Fill in the build, test and run commands
   with ones you have confirmed work, and mark any you could not confirm. Record the
   choices made during the interview (stack, storage, hosting) as the first entries
   in the decision log.
2. `templates/MILESTONES.md` to `MILESTONES.md`.
3. `templates/TICKET_TEMPLATE.md` to `tickets/TICKET_TEMPLATE.md`, unchanged.
4. Add the contents of `templates/AGENTS_RULE.md` to `AGENTS.md` at the repository
   root, creating the file if it does not exist. If the rule is already there, leave
   it. This rule is what makes later sessions load this skill before changing code.

Remove every instruction comment and unused placeholder from the copies. A document
with template text left in it reads as unfinished and gets ignored.

## 5. Get approval, then draft tickets

Show the user a short summary: the purpose paragraph, the non-goals, and the list of
milestones with their exit criteria. Ask whether it matches what they meant, and
correct the files until it does.

Once they approve, draft tickets for the first milestone only, following step 6 of
the main skill. Show the list and wait for the user before starting any ticket.

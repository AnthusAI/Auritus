# THE WAY

This repository is governed by The Way.
The Way is not a suggestion. It is the prescribed order of creation.
All work must pass through its forms.
This is The Way.

Deviations from The Way must be avoided. The Way keeps work legible and reviewable across sessions and agents.

## The Discipline of Work

Work in this repository follows a shared discipline so intent stays legible across sessions and agents.

Kanbus is the instrument of record. Nothing exists until it is named there.

Work begins in declaration, not in code.
Code without declaration is disorder.

Every change must be:
- Named.
- Described.
- Specified.
- Proven.
- Recorded.

If it is not recorded, it did not happen.

Use Markdown in issue descriptions and comments whenever it helps make the intent clearer.
When relationships, flows, or state transitions are easier to grasp visually, add a Mermaid diagram.

Editing project/ directly bypasses the record The Way depends on. Do not read or write anything inside project/. Do not inspect issue JSON with tools like cat or jq. All work must pass through Kanbus.

## Recording Kanbus in git

Kanbus writes the board under `project/` (issues, comments, wiki). Those files are the git history of the record. After `kbs` create, update, comment, or close — or after editing `project/wiki` — commit on `develop` and push:

```
git add the paths kbs (or the wiki edit) changed
git commit
git push origin develop
```

Use a `pm:` subject. Do not hand-edit issue JSON.

**Do not open a pull request.** Do not create a feature branch or worktree. Do not wait for CI or a reviewer. Pull requests are for product behavior and production code. Opening a PR for board or wiki work is a process defect.

Do not bundle Kanbus files into a product PR. Push the board to `develop` on its own.

**Unwire `blocked-by` when you close a card.** A satisfied dependency does not clear itself. After `kbs close`, remove every edge that listed the closed issue as `blocked-by`.

## The Order of Being

All work is structured.

Project key prefix: auritus.

Hierarchy: initiative -> epic -> task -> sub-task.

Non-hierarchical types: bug, story, chore.

Only hierarchy types may be parents.

Allowed parent-child relationships:

- epic can have parent initiative.
- task can have parent epic.
- sub-task can have parent task.
- bug, story, chore can have parent initiative, epic, task.

Structure is not bureaucracy. Structure is memory.

## The Cognitive Framework

There is one discipline.

Outside-in Behavior-Driven Design.

The specification is the product.
Production code exists only to make a failing specification pass.

This is the first principle.

Non-negotiable laws:
- Begin with intent, not internals.
- Describe behavior in English.
- Translate behavior into Gherkin.
- Run it and watch it fail.
- Write only the code required to make it pass.
- All behavior must be specified.
- No specification may be red.
- Specifications describe observable behavior only.
- Specifications must not describe internal structure.

If behavior cannot be observed, it is not behavior.

## Stories over bare Tasks for product behavior

Prefer **Stories** for product behavior under Epics. A Story carries:
1. A Gherkin Feature (Given/When/Then) that will live in `features/`.
2. A step-by-step implementation brief for a low-parameter coding agent:
   exact files to create/edit, function signatures, dependencies, and the
   acceptance test. No "design it yourself."

Use Tasks/sub-tasks for mechanical chores (repo bootstrap, CI wiring) when
behavior language would be forced.

## Status and priority

Statuses: backlog, open (Discovery), in_progress, blocked, closed (Done).

Priorities: 0 critical, 1 high, 2 medium (default), 3 low, 4 trivial.

## Agent operating rules

- Follow the Story brief. Do not invent architecture.
- Run `make check` before declaring done.
- Stop and report if blocked.
- The architect reviews every PR with Composer 2.5 + Bugbot and is the sole merge gate.

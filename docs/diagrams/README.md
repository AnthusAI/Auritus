# Auritus diagrams

These diagrams are source-controlled D2 files. They are the single source of
truth for the copies in `docs/diagrams/rendered/` and `site/public/diagrams/`.
The D2 sources use AWS service names and a consistent cloud boundary for the
architecture view, plus plain high-contrast shapes where the concept matters
more than a specific provider. The source format keeps the diagrams editable
while the team finalizes its icon-asset policy.

## Render the diagrams

The project pins the renderer to D2 `v0.7.1` so people and agents get the same
output. Install that version from the [D2 installation guide](https://d2lang.com/tour/install/),
then run:

```bash
make diagrams
```

If D2 is installed outside `PATH`, point the command at the pinned executable:

```bash
D2_BIN=/path/to/d2-v0.7.1/bin/d2 make diagrams
```

The command fails on a renderer version mismatch. It writes both the repository
documentation asset and the copy served by the website. Commit source and
rendered SVG changes together. SVG keeps text searchable and remains crisp in
the README, documentation pages, and at high zoom.

CI installs the same pinned D2 release, runs `make diagrams`, and fails if the
checked-in SVGs are out of date. That makes a diagram change reviewable from
the `.d2` source and repeatable without relying on a desktop drawing tool.

## Diagram catalog

| Source | Audience | Purpose |
| --- | --- | --- |
| `overview.d2` | Readers and publishers | Explain the open-model, local-first narration loop. |
| `aws-deployment.d2` | Operators | Show the AWS components and the local-worker fallback path. |
| `operator-identity-options.d2` | Operators and security reviewers | Separate the current native Cognito path from Google configuration work and the IAM Identity Center path that still needs implementation and review. |

## Guardrails for future diagrams

- Use actual deployed behavior for diagrams labelled **supported now**.
- Label proposed controls and future integrations clearly. The secure-by-design
  architecture is still being developed; do not imply that a control exists
  before its implementation and review are complete.
- Keep service names, arrows, and color meaning in nearby prose. A diagram must
  not be the only source of a security claim.
- Add new D2 files here and run `make diagrams` before linking them from the
  README or site.

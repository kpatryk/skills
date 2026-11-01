# Report & Index Templates

Copy these exactly. Consistent structure is what makes reports comparable across
issues and trustworthy to a human skimming the index.

## `report.md`

```markdown
# Diagnostic Report: [Brief Issue Title]

- **Status**: [RESOLVED | UNRESOLVED]
- **Target Machine**: [MacBook Model, Architecture, macOS Version]
- **Issue Folder**: `<issue-slug>`
- **Navigation**: [← Back to Master Index](../index.md)

---

## 1. Executive Summary

[Concise summary of the initial problem, what was found, the final outcome, and
whether the root cause was confirmed or remains a hypothesis.]

## 2. Root Cause Analysis (RCA)

- **Primary Root Cause**: [Confirmed cause, or the most probable remaining
  hypothesis if unresolved.]
- **Trigger**: [What initiated or reliably reproduces the issue.]

## 3. Chronological Attempts Log

| Attempt # | Target / Hypothesis | Command Executed | Purpose / Description | Result |
|-----------|---------------------|------------------|-----------------------|--------|
| 1 | e.g. Check sleep blockers | `pmset -g assertions` | Find processes preventing sleep | [Failed / Continued / Resolved] |
| 2 | ... | ... | ... | ... |

## 4. Raw Logs & Traces

All raw diagnostic outputs are preserved in:

- `./traces/system_logs.log`
- `./traces/command_outputs.log`

## 5. Incidental / Secondary Findings

*(Issues discovered during the investigation that did not cause the primary
symptom. Delete this section's placeholder text if there were none.)*

- [e.g. Time Machine local snapshots consuming 45 GB of APFS storage.]
- [e.g. Deprecated LaunchDaemon detected for an uninstalled third-party app.]

## 6. Lessons Learned & Preventive Recommendations

- **Lesson**: [What to watch for in the future.]
- **Preventive Maintenance**: [Recommended settings, scheduled scripts, or
  hygiene steps.]

---
[← Return to Index](../index.md)
```

## `index.md`

Maintained separately in `diagnostics/resolved/` and `diagnostics/unresolved/`.
The heading reflects which folder it lives in.

```markdown
# [Resolved | Unresolved] MacBook Issues Index

| Issue / Slug | Description | Machine / OS | Date | Action |
|--------------|-------------|--------------|------|--------|
| [m2-sleep-battery-drain](./m2-sleep-battery-drain/report.md) | Excessive overnight battery drain caused by a runaway launchd process | MacBook Air M2 / macOS 15.x | 2026-09-10 | [View Full Report](./m2-sleep-battery-drain/report.md) |

*(Every row must link to `./<issue-slug>/report.md`, and the report's own
`Issue Folder` must match that slug.)*
```

### Index maintenance rules

- Create the relevant `index.md` if it doesn't exist, with the heading and table
  header above.
- Append one row per finalized issue; newest issues can go at the bottom for a
  simple append-only history.
- Keep the description under roughly 100 characters so the table stays readable.
- The link target and the report's `Issue Folder` must always agree — that
  bidirectional link is the whole point of the index.

# Tracking procedure

This is the procedure for tracking work done by Claude Code execution sessions, which act as the machine account described in [AI contributor](ai-contributor.md), in the [Homelab Project](https://github.com/users/kevtruo/projects/1). Field definitions and labeling rules are in [Initiatives](initiatives.md#tracking).

## At every sprint plan

The two entry steps need no manual work per sprint:

| Step | Action | How |
| --- | --- | --- |
| E0a | A `Sprint` field option exists for the sprint ID, for example `portshift-3` | Automatic: the reconcile (`--apply`) creates it from the first item title that carries the sprint ID |
| E0b | The Current Sprint view shows the active sprint | One-time: the view filter is `is:open -sprint:backlog -no:sprint`, so it never names a sprint ID. Closed work shows in the History view. |

The sprint plan also names each Pilot verification step (V1, V2, and so on). A sprint cannot close until every named step is done and recorded.

## During the sprint

Each backlog item gets its own Issue in the repository that owns the change.

- **Title:** starts with the sprint ID, for example `portshift-3: Delete stale branches`.
- **Label:** the owning codeword. Set the label first, then the Initiative field to match.
- **Fields:** `Sprint` set to the sprint ID, assignee set, and the Issue added to the Project.

Each pull request follows the same rules. It closes its Issue, and its description records each convention field with evidence. A field that could not be set is reported as a gap, never claimed.

An item with no file changes (settings, web UI, or Git ref work) is done when all of these hold:

- Its Issue carries a closing comment that records what changed and how it was verified, using an API readback where possible, plus any gaps.
- Pilot-only steps are recorded as Pilot-attested, quoting the in-session confirmation and its date.
- The Issue is closed after that comment is posted.

## At sprint boundaries

At sprint planning and again at sprint review, reconcile the fields:

```bash
python3 scripts/reconcile_project_fields.py           # dry run
python3 scripts/reconcile_project_fields.py --apply   # write
```

The script needs the GitHub CLI with the `project` scope. It checks open Issues and pull requests in the Project's linked repositories, open items already in the Project from any other repository, and closed items whose title carries a sprint ID. With `--apply`, it:

- creates a missing `Sprint` option for each sprint ID whose codeword is an `Initiative` option, keeping every existing option and its ID so no item loses its value;
- sets `Initiative` from the item's codeword label;
- sets `Sprint` from the sprint ID in the title, or `backlog` if an open item's title has none;
- adds missing items from linked repositories.

The script reports gaps and leaves those items unchanged:

- no codeword label, or more than one;
- a sprint ID whose codeword is not an `Initiative` option;
- a missing `Status` on an open item;
- any draft item.

Gaps on closed items are reported but do not fail the run. The sprint review reports the result. The target is zero pending changes and zero gaps on open items. Label/field mismatches are listed in the review even after they are fixed.

## Sprint review

The review states each item's completion state as defined in the [Operating model](operating-model.md#completion-states). It also reports:

- the entry-step and Pilot verification results;
- the reconcile result;
- any unplanned settings changes, which need explicit Pilot approval;
- discovered work.

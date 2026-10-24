# Tracking procedure

This is the interim procedure for tracking work done by Claude Code execution sessions in the [Homelab Project](https://github.com/users/kevtruo/projects/1). It applies until the AI contributor identity is in place under `yeoman`. Field definitions and labeling rules are in [Initiatives](initiatives.md#tracking).

## At every sprint plan

Before work starts, two entry steps are completed and recorded:

| Step | Action | Who |
| --- | --- | --- |
| E0a | Add the sprint ID as a `Sprint` field option, for example `portshift-3` | The execution session if it can write to the Project, otherwise the Pilot |
| E0b | Update the Current Sprint view filter to the new sprint ID | The Pilot, in the web UI |

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

At sprint planning and again at sprint review, reconcile the fields on every open item:

```bash
python3 scripts/reconcile_project_fields.py           # dry run
python3 scripts/reconcile_project_fields.py --apply   # write
```

The script needs the GitHub CLI with the `project` scope. It checks open Issues and pull requests in the Project's linked repositories, and open items already in the Project from any other repository. For each item, it:

- sets `Initiative` from the item's codeword label;
- sets `Sprint` from the sprint ID in the title, or `backlog` if the title has none;
- adds missing open items from linked repositories (`--apply` only).

The script reports gaps and leaves those items unchanged:

- no codeword label, or more than one;
- a sprint ID with no matching `Sprint` option (E0a was missed);
- a missing `Status`;
- any draft item.

The sprint review reports the result. The target is zero pending changes and zero gaps on open items. Label/field mismatches are listed in the review even after they are fixed.

## Sprint review

The review states each item's completion state as defined in the [Operating model](operating-model.md#completion-states). It also reports:

- the entry-step and Pilot verification results;
- the reconcile result;
- any unplanned settings changes, which need explicit Pilot approval;
- discovered work.

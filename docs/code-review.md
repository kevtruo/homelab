# Code review

Every change to `main` in a Homelab repository arrives by pull request and passes the always-run `gate` check. The Pilot reviews each pull request against this checklist before merging. A green `gate` is necessary but does not replace review.

## Checklist

| Area | The pull request passes when |
| --- | --- |
| Scope | The change matches its Issue and the authorized sprint scope. Any deviation is named in the description. |
| Validation | The description lists the checks actually run, with results and links. "CI not run" is never a pass, and no check run is not a passing result. |
| Security impact | The description states the effect on permissions, trust, exposure and state, or why none applies. |
| Workflow changes | Actions are pinned by commit SHA. Permissions are minimal. Checkout uses `persist-credentials: false`. No new `id-token: write` without a stated reason. No `pull_request_target` with a checkout of pull request code. |
| Public repositories | The public-safety scan is clean, and the diff, title, body, branch name and commit messages were read for anything the scan cannot recognize. |
| Provenance | The Submitter field is filled. |

## Workflow changes need extra care

A pull request runs its own version of every workflow, including `gate`. A change that weakens `gate` passes its own check. Review any change under `.github/` line by line, whatever the check result.

## What `gate` checks

In this repository:

- whitespace: no trailing whitespace, carriage returns or missing final newline;
- Markdown lint;
- links: relative Markdown links resolve to a file and heading;
- public safety: the patterns in the [`CLAUDE.md`](../CLAUDE.md) "never commit" list, across tracked files, the pull request title and body, the branch name and commit messages, plus a hashed list of private names;
- workflow lint, when `.github/` changes.

In the private infrastructure repository, `gate` lints workflows, checks Terraform formatting of changed files, and enforces plan coverage: when a pull request touches the paths of a path-filtered plan workflow, `gate` fails unless that workflow succeeded on the pull request's head commit.

## Who merges

Only the Pilot merges, through the pull request.

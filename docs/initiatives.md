# Initiatives

Work in the Homelab is grouped into long-running initiatives. Each initiative has a codeword that names its sprints, labels its Issues and PRs, and scopes its sessions.

## Codewords

| Codeword | Initiative | Status | Scope |
| --- | --- | --- | --- |
| `yeoman` | Change Control | Active | Change control and repository governance |
| `quartermaster` | Cloud Foundation & Security | Active | Cloud organization, security baseline, and infrastructure as code |
| `chaff` | Honeypot | Active | Honeypot telemetry and analytics |
| `firecontrol` | Detection Engineering | Dormant | Network detection and detection-as-code |
| `signalman` | Discord Operations | Dormant | Discord operations interface |
| TBD | Agent Operations | Dormant | Future specialized agents under one orchestrator |
| `suppo` | Cost/FinOps | Dormant | Cost visibility and anomaly detection; folded into `quartermaster` |

A codeword for Agent Operations has not been assigned yet.

## Portshift

Portshift was a bounded effort to transition Homelab work from ChatGPT to Claude. It was a transition effort, not an initiative. Each new capability it produced belongs to the initiative that owns that capability.

**Status: Closed (2026-10-13).** All four done criteria are met. Portshift ran three sprints: `portshift-1` through `portshift-3`. The `portshift` label and Initiative option remain as history.

### Done criteria

| # | Criterion | Status |
| --- | --- | --- |
| 1 | portshift-1 merged | Met |
| 2 | The Homelab Project is the single tracker: every open item in every Homelab repository has Status, Initiative and Sprint, status updates are automatic, and nothing sensitive is public | Met |
| 3 | ChatGPT-era code tracking is retired, and Claude Code tracking is in place | Met |
| 4 | Closeout record merged in this document | Met |

### Closeout record

**Criterion 1 — Met (2026-10-12).** The Claude operating baseline merged: initiative codewords and work IDs ([#2](https://github.com/kevtruo/homelab/pull/2), [#7](https://github.com/kevtruo/homelab/pull/7)), and the operating model, repository boundaries and `CLAUDE.md` ([#8](https://github.com/kevtruo/homelab/pull/8)). The matching changes for the private repository are recorded in the private infrastructure repository.

**Criterion 2 — Met (2026-10-13).** The [Homelab Project](https://github.com/users/kevtruo/projects/1) is the single tracker:
- Fields: Initiative and Sprint ([#9](https://github.com/kevtruo/homelab/issues/9)).
- Workflows and views: auto-add, Backlog on add, Done on close and on merge, and the Board, Current Sprint and History views ([#10](https://github.com/kevtruo/homelab/issues/10)).
- A sanitized Project README ([#11](https://github.com/kevtruo/homelab/issues/11)).
- Field rules ([#12](https://github.com/kevtruo/homelab/issues/12), [#13](https://github.com/kevtruo/homelab/pull/13)).

On 2026-10-13, merged pull requests were observed moving to Done automatically, including [#18](https://github.com/kevtruo/homelab/pull/18). The first field reconcile found zero Initiative or Sprint gaps on open items. Items from the private repository are visible only to the owner; that evidence is recorded in the private infrastructure repository.

**Criterion 3 — Met (2026-10-13).** The custom GitHub App used by the earlier ChatGPT/Codex contributor workflow has been deleted, and its local token tooling has been removed. The interim tracking procedure is documented in [Tracking procedure](tracking.md) ([#18](https://github.com/kevtruo/homelab/pull/18)) and was first run on 2026-10-12. Supporting evidence for the private repository is recorded in the private infrastructure repository.

**Criterion 4 — Met (2026-10-13).** This record ([#17](https://github.com/kevtruo/homelab/issues/17)).

Follow-on work belongs to `yeoman`: the Claude GitHub App as the AI contributor identity, and branch hygiene.

## ID convention

Work IDs take the form `<codeword>-<n>` in lowercase, where `n` is the sprint number, for example `yeoman-1` or `portshift-1`. Each sprint runs in one execution session.

## Labels

Each codeword, and `portshift`, has a matching GitHub label of the same name. Issues and PRs carry the label of the initiative or effort that owns the work.

Sprints do not have labels. The sprint ID appears at the start of each sprint Issue and PR title, for example `portshift-1: Record initiative naming and labels`.

## Tracking

The [Homelab Project](https://github.com/users/kevtruo/projects/1) is the single tracker for all Homelab work. Items from private repositories are visible only to the owner. Field names, option names, views and the Project README are public, so they stay generic. The Project has no draft items.

| Field | Meaning |
| --- | --- |
| Status | `Backlog`, `Ready`, `In Progress` or `Done`. Closed Issues and merged PRs move to `Done` automatically. |
| Initiative | The codeword of the owning initiative, or `portshift`. One option per codeword. |
| Sprint | The sprint ID, for example `portshift-2`. Open items not yet in a sprint use `backlog`. Options for closed sprints are kept as history. |

The Project has no Priority field.

The codeword label is authoritative, and the Initiative field mirrors it. Whoever creates an Issue or PR sets the label first, then sets the field to match. Each sprint review reports any label/field mismatches.

The [Tracking procedure](tracking.md) covers sprint entry steps, the field reconcile at sprint boundaries, and sprint review.

## Legacy mapping

Earlier work used prefix-based IDs. Legacy IDs are history: they remain valid references and are not renamed. This mapping is final as of the Portshift closeout; new work uses codeword sprint IDs only.

| Legacy prefix | Codeword |
| --- | --- |
| GC, DEV | `yeoman` |
| AWS | `quartermaster` |
| DSA | `chaff` |
| DET | `firecontrol` |
| DOPS | `signalman` |
| AGENT | TBD (Agent Operations) |

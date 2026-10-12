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

Portshift is a bounded effort to transition Homelab work from ChatGPT to Claude. It is a transition effort, not an initiative. Any new capability it produces belongs to the initiative that owns that capability. Portshift closes when its done criteria are met.

### Done criteria

| # | Criterion | Status |
| --- | --- | --- |
| 1 | portshift-1 merged | Met |
| 2 | The Homelab Project is the single tracker: every open item in every Homelab repository has Status, Initiative and Sprint, status updates are automatic, and nothing sensitive is public | In progress (portshift-2) |
| 3 | ChatGPT-era code tracking is retired, and Claude Code tracking is in place | Not started (portshift-3) |
| 4 | Closeout record merged in this document | Not started |

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

## Legacy mapping

Earlier work used prefix-based IDs. Legacy IDs are history: they remain valid references and are not renamed.

| Legacy prefix | Codeword |
| --- | --- |
| GC, DEV | `yeoman` |
| AWS | `quartermaster` |
| DSA | `chaff` |
| DET | `firecontrol` |
| DOPS | `signalman` |
| AGENT | TBD (Agent Operations) |

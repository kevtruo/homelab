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

## ID convention

Work IDs take the form `<codeword>-<n>` in lowercase, where `n` is the sprint number, for example `yeoman-1` or `portshift-1`. Each sprint runs in one execution session.

## Labels

Each codeword, and `portshift`, has a matching GitHub label of the same name. Issues and PRs carry the label of the initiative or effort that owns the work.

Sprints do not have labels. The sprint ID appears at the start of each sprint Issue and PR title, for example `portshift-1: Record initiative naming and labels`.

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

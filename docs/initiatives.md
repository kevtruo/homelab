# Initiatives

Work in the Homelab is grouped into long-running initiatives. Each initiative has a codeword that names its work and scopes its sessions.

## Codewords

| Codeword | Initiative | Status | Scope |
| --- | --- | --- | --- |
| `yeoman` | Change Control | Active | Contribution workflow, review, and merge controls |
| `quartermaster` | Cloud Foundation & Security | Active | Cloud accounts, identity, governance, security baselines, and cost |
| `chaff` | Honeypot | Active | Honeypot sensors and the telemetry they collect |
| `firecontrol` | Detection Engineering | Dormant | Detection content, testing, and validation |
| `signalman` | Discord Operations | Dormant | Change awareness and bounded automation through Discord |
| TBD | Agent Operations | Dormant | Agent identities, access, and execution boundaries |
| `suppo` | Cost/FinOps | Dormant | Folded into `quartermaster` |

A codeword for Agent Operations has not been assigned yet.

## Portshift

Portshift is a bounded effort to transition Homelab work from ChatGPT to Claude. It is not an initiative. Any new capability it produces belongs to the initiative that owns that capability. Portshift closes when its done criteria are met.

## ID convention

Work IDs take the form `<codeword>-<n>` in lowercase, for example `yeoman-1` or `portshift-1`. Each ID corresponds to a single execution session.

## Legacy mapping

Earlier work used prefix-based IDs. Those IDs remain valid as history and are not renamed.

| Legacy prefix | Codeword |
| --- | --- |
| GC, DEV | `yeoman` |
| AWS | `quartermaster` |
| DSA | `chaff` |
| DET | `firecontrol` |
| DOPS | `signalman` |
| AGENT | TBD (Agent Operations) |

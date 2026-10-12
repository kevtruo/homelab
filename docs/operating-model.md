# Operating model

## Philosophy

Work is architect-directed, agent-executed, PR-gated, and human-authorized. Design decisions come from people, agents carry out scoped work, every change arrives as a pull request, and a human decides what merges and deploys.

## Roles

| Role | Responsibility |
| --- | --- |
| Captain | Authorizes work, reviews pull requests, and merges |
| Architecture | Designs the system and records design decisions |
| Orchestrator | Maintains the roadmap, plans sprints, and prepares handoffs |
| Execution session | A Claude Code session that carries out one sprint and stops at the pull request |

## Flow

1. Sprint planning
2. Issues
3. Branches
4. Pull requests
5. CI validation
6. Human review
7. Human merge
8. Deployment workflow
9. Runtime verification
10. Close

## Completion states

Each state is distinct, and reaching one does not imply the next:

| State | Meaning |
| --- | --- |
| Implemented | The change exists on a branch |
| PR opened | The change is proposed for review |
| CI passed | Automated validation succeeded |
| Merged | A human accepted the change into the main branch |
| Deployed | The deployment workflow applied the change |
| Runtime-verified | The running environment was checked and matches the intent |
| Accepted | The outcome was confirmed against the acceptance criteria |

An AI summary is not deployment evidence. Completion is claimed only from the system of record that proves it.

## Systems of record

| System | Records |
| --- | --- |
| GitHub Issues | Work |
| GitHub Projects | Tracking |
| Commits and pull requests | History and review |
| GitHub Actions | Validation and deployment |
| Cloud provider | Runtime state |

Discord is the human-facing notification interface. It is never authoritative.

## Infrastructure model

Terraform is authoritative for infrastructure. A plan runs on each pull request. Apply runs only after a human merge, through CI with short-lived OIDC credentials. Some environments add a manual approval gate tied to the exact merged commit. There are no long-lived deploy keys.

Human access is read-only by default. Root and break-glass access is reserved.

## Initiative scopes

Codewords, statuses, and ID conventions are listed in [Initiatives](initiatives.md).

**yeoman (Change Control).** Change control and repository governance: how work is proposed, reviewed, merged, and recorded across the Homelab repositories.

**quartermaster (Cloud Foundation & Security).** The cloud organization, its security baseline, and the infrastructure as code that defines them.

**chaff (Honeypot).** Honeypot telemetry and the analytics built on it.

**firecontrol (Detection Engineering).** Network detection and detection-as-code: detection content managed, tested, and validated like source code.

**signalman (Discord Operations).** The Discord operations interface, which delivers human-facing notifications and awareness of change.

**Agent Operations (codeword TBD).** Future specialized agents working under one orchestrator.

**suppo (Cost/FinOps).** Cost visibility and anomaly detection. This work is folded into quartermaster.

**portshift.** A bounded transition effort, not an initiative. It moves Homelab operations from ChatGPT to Claude, and any capability it produces belongs to the owning initiative.

## Principles

- **Infrastructure as code.** Infrastructure is defined in code and changed through review.
- **Least privilege.** Identities receive only the access their task requires.
- **Human authorization.** People authorize merges and deployments.
- **Cost consciousness.** The lab runs on a small personal budget, with no always-on infrastructure unless it is needed.
- **Discord observability.** People learn about changes through Discord notifications.
- **Durable engineering history.** Decisions and evidence live in Issues, commits, and pull requests.
- **Incremental delivery.** Work ships in small, reviewable units.
- **Public/private confidentiality.** Public material is sanitized, and implementation detail stays private.
- **Evidence-based completion.** Work is complete only when evidence shows it.

# AI contributor

This page describes how an AI agent contributes code to Homelab repositories as a bot, and the guardrails around it. The model was first proved in a private sandbox repository under `yeoman-1`. Implementation detail and evidence are recorded in the private infrastructure repository.

## Identity and trigger model

- **Identity:** Anthropic's official Claude GitHub App. Commits and pull requests are authored by the App's bot account, not by the operator.
- **Runner:** the official Claude Code GitHub Action, in a GitHub Actions workflow in the target repository.
- **Trigger:** the operator mentions `@claude` in an Issue or pull request comment. Comments from other accounts do not start the job.
- **Model access:** the operator's Claude subscription, through an OAuth token stored as an encrypted Actions secret. If the token is exposed, the operator revokes and reissues it.
- **Output:** the bot works on its own branch, pushes commits, and opens a pull request. Review and merge stay with the operator.

## Guardrails

| ID | Guardrail |
| --- | --- |
| G1 | The workflow requests an OIDC token only because the action's App authentication requires it. |
| G2 | No cloud-provider trust policy may accept a token from the AI contributor workflow. This is enforced on the cloud side, separately from the repository. |
| G3 | The agent's tools are restricted in the workflow: read and search, file edits inside the checkout, commit and a constrained push, its own status comment, and pull request creation. It has no general shell, no web access, and no merge, settings, or webhook tools. |
| G4 | Only the operator can trigger the workflow. Actions are pinned by commit SHA. Turns and job time are capped. Workflow permissions are limited to contents, pull requests, and issues write, plus the OIDC token. |
| G5 | Bot-authored pull requests need the operator's formal approval. The bot cannot merge. A new commit dismisses an existing approval. |
| G6 | GitHub requires an App's permissions to be accepted as a set. The official App's set includes workflow write, so the effect is tested and treated as a design input. |

Branch rules on the default branch, not the bot's own restraint, enforce G5: one required approval, stale-approval dismissal, a required CI check, and updates only through a pull request merged by an administrator. The App is not a bypass actor.

## Test results

<!-- Filled in from the yeoman-1 test matrix once it has run. -->

| Test | Result |
| --- | --- |
| Bot opens a pull request as its own identity | pending |
| CI runs on the bot's pull request | pending |
| Operator can be requested as reviewer and approve | pending |
| Bot merge denied before approval | pending |
| Bot merge denied after approval | pending |
| New bot commit dismisses the approval | pending |
| Operator merges through the pull request | pending |
| Effective App token permissions; workflow edits on a bot branch | pending |
| Trigger restriction | config-verified, not runtime-tested |
| Bot asked to create a webhook or change settings | pending |

## Known gaps

- The bot merge-denial tests exercise the agent's tool restriction. The tool list has no merge tool, so these tests do not show GitHub denying a merge attempted with the App's token.
- Trigger restriction is verified from configuration only; no second account was used.
- The App's permission set is broader than the workflow uses. Its runtime effect is recorded in the test results.

## Reuse notes

- **Production branch rules (`yeoman-2`):** reuse the sandbox rule set: required approval, stale-approval dismissal, a required CI check, and administrator-only updates through a pull request. Decide separately whether to test GitHub-side denial of an App-token merge.
- **Wider rollout (`yeoman-3` onward):** install the App per repository, never organization-wide. Copy the workflow with its actor check, SHA pins, limits, and tool list. Review the tool list in the pull request that adds it. Keep cloud trust policies from matching the AI contributor workflow (G2) before installing the App in any repository that deploys.

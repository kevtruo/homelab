# AI contributor

This page describes how an AI agent contributes code to Homelab repositories as a bot, and the guardrails around it. The model was first proved in a private sandbox repository under `yeoman-1`. Implementation detail and evidence are recorded in the private infrastructure repository.

## Identity and trigger model

- **Identity:** Anthropic's official Claude GitHub App. Commits and pull requests are authored by the App's bot account, not by the operator.
- **Runner:** the official Claude Code GitHub Action, in a GitHub Actions workflow in the target repository.
- **Trigger:** the operator mentions `@claude` in an Issue or pull request comment. Comments from other accounts, including the bot's own, do not start the job.
- **Model access:** the operator's Claude subscription, through an OAuth token stored as an encrypted Actions secret. If the token is exposed, the operator revokes and reissues it.
- **Output:** the bot works on its own branch, pushes commits, and opens a pull request. Review and merge stay with the operator.

## Guardrails

| ID | Guardrail |
| --- | --- |
| G1 | The workflow requests an OIDC token only because the action's App authentication requires it. The action removes the OIDC request variables from the agent's environment. |
| G2 | No cloud-provider trust policy may accept a token from the AI contributor workflow. This is enforced on the cloud side, separately from the repository. |
| G3 | The agent's tools are restricted in the workflow: read and search, file edits inside the checkout, commit and a constrained push, its own status comment, and pull request creation. It has no general shell, no web access, and no merge, settings, or webhook tools. |
| G4 | Only the operator can trigger the workflow. Actions are pinned by commit SHA. Turns and job time are capped. Workflow permissions are limited to contents, pull requests, and issues write, plus the OIDC token. |
| G5 | Bot-authored pull requests need the operator's formal approval. The bot cannot merge. A new commit dismisses an existing approval. |
| G6 | GitHub requires an App's permissions to be accepted as a set. The official App's set includes workflow write, so the effect was tested (see results). |

Branch rules on the default branch, not the bot's own restraint, enforce G5: one required approval, stale-approval dismissal, a required CI check, and updates only through a pull request merged by an administrator. The App is not a bypass actor.

## Test results

| Test | Result |
| --- | --- |
| Bot opens a pull request as its own identity | Pass |
| CI runs on the bot's pull request | Pass |
| Operator can be requested as reviewer and approve | Pass |
| Bot merge denied before approval | Pass, by tool restriction |
| Bot merge denied after approval | Pass, by tool restriction |
| New bot commit dismisses the approval | Pass |
| Operator merges through the pull request | Pass |
| Bot edits a workflow file on its branch | GitHub rejected the push: the App token used at runtime has no workflow write, so nothing ran |
| Trigger restriction | Config-verified, not runtime-tested. The bot's own comments never triggered a run. |
| Bot asked to create a webhook and change settings | Refused; nothing changed |

## Findings

- **Job token left in the checkout.** Newer versions of the checkout action store the job token in a form the Claude action did not remove. The job token stayed usable by git during the agent session, and one bot push used it. Fixed by pinning a checkout version whose credential the action removes, then verified in the run log. Recheck this whenever either action is upgraded.
- **Commit attribution.** By default the action attributed commits to the generic Actions bot rather than the Claude bot. Fixed by setting the bot user ID explicitly.
- **Pull request creation.** The action's built-in prompt prefers posting a "create PR" link. Opening the PR directly needed an explicit instruction in the workflow.
- **Token entry.** A subscription token copied from a wrapped terminal line picked up a line break and failed authentication. Strip whitespace when storing it.
- **Permission suggestions.** When blocked, the bot suggested granting it more permissions or gave the operator commands to do the blocked action. Its statements about its own permissions were not always accurate. Treat such suggestions as untrusted and change the tool list only through a reviewed pull request.
- **Every merge is a bypass.** An administrator-only update rule makes every merge to the default branch an administrator bypass, even an approved one. The audit trail then can't tell a normal merge from one that skipped approval.

## Known gaps

- The bot merge-denial tests exercise the agent's tool restriction. The tool list has no merge tool, so these tests do not show GitHub denying a merge attempted with the App's token.
- The webhook test exercises the agent's refusal, not GitHub's enforcement of the App token's permissions.
- Trigger restriction is verified from configuration only; no second account was used.
- The runtime token's lack of workflow write comes from the token exchange the action uses, not from any repository control, and may change.
- Bot commits are unsigned.

## Reuse notes

- **Production branch rules (`yeoman-2`):** reuse the sandbox rule set: required approval, stale-approval dismissal, a required CI check. Decide whether to keep an administrator-only update rule, given the bypass audit gap. Decide whether to test GitHub-side denial of an App-token merge, and whether to require signed commits.
- **Wider rollout (`yeoman-3` onward):** install the App per repository, never organization-wide. Copy the workflow with its actor check, SHA pins, limits, tool list, bot identity setting, and checkout pin. Before each rollout, confirm in a run log that the checkout credential is removed. Keep cloud trust policies from matching the AI contributor workflow (G2) before installing the App in any repository that deploys.

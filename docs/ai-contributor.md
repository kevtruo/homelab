# AI contributor

AI contributions to Homelab repositories come from Claude Code execution sessions. A session acts as a machine account, `claude-coworker`, which the operator controls. It works on a branch, opens a pull request, and names itself as the submitter. The operator reviews and approves every pull request before merging it. The bot contributor model, where an App account authors pull requests, was proven in a private sandbox repository under `yeoman-1`. It is not used in production.

## Production model

- **Contributor:** a Claude Code execution session, working within the sprint scope the Pilot authorized.
- **GitHub author:** `claude-coworker`, a machine account the operator controls. It is a collaborator with write access, not an administrator, so it cannot change repository settings or rulesets.
- **Pull requests:** author and assignee `claude-coworker`; the operator is requested as reviewer.
- **Submitter record:** every pull request carries a `Submitter` field, `claude-coworker (Claude Code session), <session link>`. Commits are authored as `Claude <noreply@anthropic.com>`, never with the account's own no-reply address, so the account's user ID stays out of public history.
- **Approval:** the operator approves every machine-account pull request before merging; a merge with no approval on record is not done. Sessions never approve or merge, even though write access would allow it. This is policy: GitHub cannot stop a collaborator's approval from counting.
- **No bot:** no AI contributor App is installed and no AI contributor workflow runs in production repositories.

## Why a machine account, not a bot

- **Formal review without an App.** A separate account lets the operator be requested as reviewer and approve formally, without installing an App or running an agent in Actions.
- **The gate is the control.** What protects `main` is that every change arrives by pull request, passes the always-run `gate` check, and is reviewed against the [code review standard](code-review.md). The author's identity is not the control.
- **Less to defend.** The bot model needs an App whose permission set includes workflow write, a model access token stored as a secret, and an OIDC token request in the workflow (G1, G2 and G6 below). A machine account needs none of these.

## Production rules

Each Homelab repository has two rulesets on its default branch. They are split because a bypass applies to every rule in its ruleset: the required check sits in a ruleset with no bypass, so no merge can skip it.

| Ruleset | Rule | Setting |
| --- | --- | --- |
| Review | Pull request | Required, with 1 approval. A new commit dismisses an existing approval. Conversations must be resolved. An unattributed Copilot pull request needs one extra approval. |
| Review | Force pushes | Blocked |
| Review | Deletion | Restricted |
| Review | Bypass | The repository administrator role, for pull requests only. No other actor. |
| Gate | Required status check | `gate` only, reported by GitHub Actions |
| Gate | Bypass | None |

Not used: code owner review, required signed commits, and an update restriction rule.

A machine-account pull request merges through the operator's approval and a passing `gate`, with no bypass. The administrator bypass is for pull requests the operator authors, and it skips only the review rules. Because the bypass works only through a pull request, direct pushes, force pushes and deletion of the default branch stay blocked for everyone.

There is no update restriction rule. The sandbox showed that an administrator-only update rule makes every merge a bypass and hides a skipped approval among normal merges.

Rulesets on a private repository need a paid GitHub plan. On the free plan, neither rulesets nor protected branches apply to private repositories.

`gate` runs on every pull request with no path filters. It has no cloud access, its actions are pinned by commit SHA, and checkout does not persist credentials. In the private infrastructure repository it also enforces plan coverage: a pull request that touches a plan workflow's paths cannot pass `gate` until that plan has succeeded on its head commit. The checks in each repository are listed in the [code review standard](code-review.md#what-gate-checks).

## Sandbox record (`yeoman-1`)

The rest of this page records the bot model as it was tested in the sandbox. Implementation detail and evidence are recorded in the private infrastructure repository.

### Identity and trigger model

- **Identity:** Anthropic's official Claude GitHub App. Commits and pull requests are authored by the App's bot account, not by the operator.
- **Runner:** the official Claude Code GitHub Action, in a GitHub Actions workflow in the target repository.
- **Trigger:** the operator mentions `@claude` in an Issue or pull request comment. Comments from other accounts, including the bot's own, do not start the job.
- **Model access:** the operator's Claude subscription, through an OAuth token stored as an encrypted Actions secret. If the token is exposed, the operator revokes and reissues it.
- **Output:** the bot works on its own branch, pushes commits, and opens a pull request. Review and merge stay with the operator.

### Guardrails

| ID | Guardrail |
| --- | --- |
| G1 | The workflow requests an OIDC token only because the action's App authentication requires it. The action removes the OIDC request variables from the agent's environment. |
| G2 | No cloud-provider trust policy may accept a token from the AI contributor workflow. This is enforced on the cloud side, separately from the repository. |
| G3 | The agent's tools are restricted in the workflow: read and search, file edits inside the checkout, commit and a constrained push, its own status comment, and pull request creation. It has no general shell, no web access, and no merge, settings, or webhook tools. |
| G4 | Only the operator can trigger the workflow. Actions are pinned by commit SHA. Turns and job time are capped. Workflow permissions are limited to contents, pull requests, and issues write, plus the OIDC token. |
| G5 | Bot-authored pull requests need the operator's formal approval. The bot cannot merge. A new commit dismisses an existing approval. |
| G6 | GitHub requires an App's permissions to be accepted as a set. The official App's set includes workflow write, so the effect was tested (see results). |

In the sandbox, branch rules on the default branch, not the bot's own restraint, enforce G5: one required approval, stale-approval dismissal, a required CI check, and updates only through a pull request merged by an administrator. The App is not a bypass actor.

### Test results

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

### Findings

- **Job token left in the checkout.** Newer versions of the checkout action store the job token in a form the Claude action did not remove. The job token stayed usable by git during the agent session, and one bot push used it. Fixed by pinning a checkout version whose credential the action removes, then verified in the run log. Recheck this whenever either action is upgraded.
- **Commit attribution.** By default the action attributed commits to the generic Actions bot rather than the Claude bot. Fixed by setting the bot user ID explicitly.
- **Pull request creation.** The action's built-in prompt prefers posting a "create PR" link. Opening the PR directly needed an explicit instruction in the workflow.
- **Token entry.** A subscription token copied from a wrapped terminal line picked up a line break and failed authentication. Strip whitespace when storing it.
- **Permission suggestions.** When blocked, the bot suggested granting it more permissions or gave the operator commands to do the blocked action. Its statements about its own permissions were not always accurate. Treat such suggestions as untrusted and change the tool list only through a reviewed pull request.
- **Every merge is a bypass.** An administrator-only update rule makes every merge to the default branch an administrator bypass, even an approved one. The audit trail then can't tell a normal merge from one that skipped approval.

### Known gaps

- The bot merge-denial tests exercise the agent's tool restriction. The tool list has no merge tool, so these tests do not show GitHub denying a merge attempted with the App's token.
- The webhook test exercises the agent's refusal, not GitHub's enforcement of the App token's permissions.
- Trigger restriction is verified from configuration only; no second account was used.
- The runtime token's lack of workflow write comes from the token exchange the action uses, not from any repository control, and may change.
- Bot commits are unsigned.

### If the bot model is reconsidered

- Install the App per repository, never organization-wide.
- Copy the sandbox workflow with its actor check, SHA pins, limits, tool list, bot identity setting and checkout pin, and confirm in a run log that the checkout credential is removed.
- Keep cloud trust policies from matching the AI contributor workflow (G2) before installing the App in any repository that deploys.

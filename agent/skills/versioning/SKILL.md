---
name: versioning
description: Use when cutting a release, bumping the repo version, updating the changelog, or publishing a release branch, tag, or release pull request.
---

# Versioning

`VERSION` at repo root holds the current release (`0.1.0`). `CHANGELOG.md` has `## [Unreleased]` plus one `## [X.Y.Z] - date` section per release.

## Cutting a release

Steps 1-5 are the whole release. Everything stays local: no push, no pull request.

1. Branch from the default branch before any edit: `git switch -c release/X.Y.Z`.
2. Move `Unreleased` entries under a new `## [X.Y.Z] - <today>` heading.
3. Write the number into `VERSION` (no `v` prefix; the git tag adds it: `0.1.0` → `v0.1.0`).
4. Commit the version files and any doc updates on the release branch: `git commit -m "chore: release X.Y.Z"`.
5. Tag the release commit: `git tag vX.Y.Z`. The release is finished — stop here.

## Publishing

The release does not leave this machine until the user answers two questions:

- which remote and branch receive it — propose `origin` and `release/X.Y.Z`;
- whether to open a pull request.

Ask with the `ask` tool in a session; in a chain, the approval gate on the publish step carries the same two questions. Then run:

```bash
git push -u <remote> release/X.Y.Z && git push <remote> vX.Y.Z
gh pr create --base main --head release/X.Y.Z \
  --title "Release vX.Y.Z" --body "<the new changelog section>"
```

The second command runs only when they asked for a pull request. `main` receives the release only when that pull request merges.

## Rules

- Minor for features, patch for fixes. While `0.x`, major only for breaking dotfile layout changes.
- `agent/config.yml` `setupVersion` is harness-internal — never bump it for repo releases.
- No `v` prefix inside files; tags carry the `v`.
- Never push a release commit or tag straight to `main`.
- No answer, no push: publishing starts with the question, and the proposed defaults are what you offer in it.
- `gh pr create` missing or failing? Leave the pushed branch in place, report the exact error, and stop. Never fall back to pushing `main`.

## Common mistakes

- Asking the two questions and pushing in the same turn → the push waits for the answer.
- Pushing the branch or tag "on the skill's defaults" instead of asking → the defaults are the question's proposal, not permission.
- `git push origin main`, or a plain `git push` while on `main`, during a release → wrong branch; move the commit to `release/X.Y.Z` and restart at step 1.
- Editing `CHANGELOG.md` or `VERSION` before creating the release branch → the branch is step 1 for that reason.
- Changelog section without `VERSION` bump → keep them in sync in one commit.
- Tagging before committing the version files → tag after the commit.
- Pushing the tag without the branch → push both, or the pull request has nothing to review.

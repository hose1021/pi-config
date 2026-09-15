# pi-config

Personal configuration for the [pi](https://github.com/earendil-works/pi) coding
agent. The repository root is `~/.pi`. The live agent directory is `agent/`,
which is the default pi config directory.

Version: see `VERSION`.

## Layout

- `agent/settings.json` — main settings: provider, model, theme, npm packages.
- `agent/agents/` — subagent definitions: `planner`, `reviewer`, `scout`,
  `worker`.
- `agent/extensions/` — TypeScript extensions. pi loads them at runtime.
- `agent/skills/` — skill instruction files.
- `agent/themes/` — theme JSON files.
- `agent/npm/` — install root for npm pi packages.
- `agent/append_system.md` — system prompt appendix.
- `agent/pretty-tui.json` — config for the `pi-pretty-tui` package.
- `AGENTS.md` — rules for agents that work in this repository.
- `.codegraph/` — CodeGraph index. Machine-local, gitignored.
- `VERSION`, `CHANGELOG.md` — release number and release history.

Live state under `agent/` is gitignored: `auth.json`, `sessions/`,
`models-store.json`, `pi-cpa.json`, `bin/`, `web-search-cache/`, `trust.json`,
and `cache/`. It never enters a commit.

## Install

```bash
git clone https://github.com/hose1021/pi-config.git ~/.pi
cd ~/.pi/agent/npm && npm install
```

Set `PI_CODING_AGENT_DIR` to this `agent/` directory when the clone is not at
`~/.pi`.

## Validate

```bash
cd agent/extensions && pnpm exec tsc --noEmit
```

This is the only static check. There is no test suite.

## Release

A release updates `VERSION` and `CHANGELOG.md` on a `release/X.Y.Z` branch,
then tags the release commit `vX.Y.Z`. The steps are in
`agent/skills/versioning/SKILL.md`.

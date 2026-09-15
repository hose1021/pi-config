# Changelog

## [Unreleased]

## [0.1.0] - 2026-09-15

First versioned release of this pi agent configuration.

### Added

- All pi configuration under `agent/`: `settings.json`, `agents/`,
  `extensions/`, `skills/`, `themes/`, `npm/`.
- Extensions: `ask-user-question`, `browser`, `codegraph-enhanced`,
  `custom-header`, `dcg-guard`, `interactive-subagents`,
  `observational-memory`, `prompt-snippets`, `subagent`, `web-fetch`,
  `web-search`.
- Subagent definitions under `agent/agents/`: `planner`, `reviewer`, `scout`,
  `worker`.
- 61 skills under `agent/skills/`.
- Theme `rainbow-prism`.
- `AGENTS.md` with the repository rules for agents.

### Changed

- Skills and themes moved from the repository root into `agent/`. The
  repository root is now the live pi agent directory.
- `.gitignore` ignores live runtime state by explicit path under `agent/`
  (`auth.json`, `sessions/`, `models-store.json`, `pi-cpa.json`, `bin/`,
  `web-search-cache/`, `trust.json`, `cache/`) instead of the whole `agent/`
  directory.

### Removed

- Root `README.md` and `assets/thumbnail.png`.
- Root `skills/` and `themes/`, replaced by `agent/skills/` and
  `agent/themes/`.

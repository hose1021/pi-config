# Changelog

## [Unreleased]

## [0.2.0] - 2026-09-15

### Added

- `todo` extension: the `todo` tool and the `/todos` command.
- `README.md`, describing the repository layout.
- `codegraph_*` in the `planner` subagent tool list, so the planner can query
  the index directly.

### Changed

- `AGENTS.md` rewritten against the current repository state: extension
  inventory, extension enablement, the two subagent sets, validation steps,
  CodeGraph behaviour, config and state files, git conventions.
- `agent/append_system.md` renamed to `agent/APPEND_SYSTEM.md`. pi reads the
  uppercase name only, and a lowercase file is ignored on a case-sensitive
  filesystem.

### Fixed

- `codegraph-enhanced`: the CodeGraph loader is now set from a synchronous
  index check. The async status call raced the first turn, so the tool list
  never held `codegraph_load` and the `before_agent_start` guidance never
  fired. The resolved phase stays authoritative.
- `README.md`: the `append_system.md` path corrected to `APPEND_SYSTEM.md`.

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

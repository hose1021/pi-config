# AGENTS.md — pi-config

Personal configuration for **pi**, the coding agent. The repository root is
`~/.pi`. The live agent directory is `agent/`, which is pi's default config
directory.

This is NOT the pi source. Do not edit files under `node_modules/`, and do not
assume pi internals beyond the documented `@earendil-works/pi-*` extension APIs.

Remote: `https://github.com/hose1021/pi-config.git`. Branch: `release/0.1.0`.
Version: `VERSION`. Changes: `CHANGELOG.md`.

## Layout

- `agent/APPEND_SYSTEM.md` — system prompt appendix. Holds the workflow rules
  (Planning, Implementation, Research, Agents, Tools, Output). pi reads this
  exact uppercase name. A lowercase `append_system.md` is ignored on a
  case-sensitive filesystem.
- `agent/extensions/` — custom TypeScript extensions and extension folders.
- `agent/agents/` — subagent definitions: `planner.md`, `reviewer.md`,
  `scout.md`, `worker.md`.
- `agent/skills/` — skill instruction files, one folder per skill.
- `agent/themes/` — theme JSON files. Currently `rainbow-prism.json`.
- `agent/npm/` — install root for npm pi packages. Tracked `package.json`,
  gitignored `node_modules/`.
- `agent/settings.json` — main pi settings.
- `agent/pretty-tui.json` — config for the `pi-pretty-tui` package.
- `agent/web-search.json` — config for the `web-search` extension. Untracked.
- `.codegraph/` — CodeGraph index database. Machine-local.
- `README.md`, `AGENTS.md`, `CHANGELOG.md`, `VERSION`, `.gitignore`.

There is no `agent/prompts/` directory and no `LICENSE` file.

## Extensions

pi auto-discovers every entry under `agent/extensions/` and loads its
`index.ts`. A bare `.ts` file works as well as a folder. The TypeScript source
runs directly: there is no build step and no committed `dist/`. Do not add one.

- `browser/` — Playwright-driven headless Chromium tools (`browser_goto`,
  `browser_eval`, `browser_console`, and more). Original to this repo.
- `codegraph-enhanced/` — CodeGraph structural-analysis tools and indexing
  controls. Fork of `EstebanForge/pi-codegraph-enhanced`. Carries `LOCAL PATCH`
  markers.
- `custom-header.ts` — replaces the built-in startup header with an editable
  copy. Original.
- `dcg-guard.ts` — routes every `bash` tool call through
  `dcg --robot test <command>` and blocks the call when dcg denies it. Official
  recipe from `Dicklesworthstone/destructive_command_guard`
  (`docs/pi-integration.md`).
- `prompt-snippets/` — toggle menu (`alt+s`, `/snippets`) over the markdown
  snippets in `prompt-snippets/snippets/`. Original.
- `subagent/` — spawns an isolated `pi` process per subagent invocation.
  Original to this repo, based on the pi extension examples.
- `todo/` — the `todo` tool and the `/todos` command. From pi
  `examples/extensions/todo.ts` (upstream, MIT).
- `web-fetch/` — fetches URL content. Original.
- `web-search/` — web search. Original. Disabled, see below.
- `ask-user-question.ts` — structured questions. Original. Disabled, see below.
- `interactive-subagents/` — placeholder only. A `README.md` pointing at
  `amosblomqvist/pi-interactive-subagents`. No code.
- `observational-memory/` — placeholder only. A `README.md` pointing at
  `amosblomqvist/pi-observational-memory`. No code.

Two entries break the "one shared `package.json`" rule and carry their own
dependency tree and lockfile: `browser/` and `web-fetch/`. Treat that as the
existing state, not as the convention to copy.

Imports are inconsistent. `ask-user-question.ts`, `web-fetch/index.ts`, and
`web-search/index.ts` import from `@mariozechner/pi-coding-agent`. The rest
import from `@earendil-works/pi-coding-agent`. Match the surrounding file.

Conventions when editing or adding an extension:

- One entry per extension. Default-export the entry function:

  ```ts
  export default function name(pi: ExtensionAPI) { ... }
  ```

- Register commands, shortcuts, event handlers, and message renderers through
  the `ExtensionAPI` argument.
- `@earendil-works/pi-coding-agent`, `@earendil-works/pi-ai`, and
  `@earendil-works/pi-tui` are peer packages supplied by the pi host at
  runtime. Never vendor a local copy: a duplicate module instance breaks
  `instanceof` checks and event typing.
- Prefer pure helpers (exported, no side effects). They stay testable and they
  appear in CodeGraph.
- Preserve `LOCAL PATCH` markers and upstream attribution in every forked
  extension.

## Extension enablement

The `extensions` array in `agent/settings.json` holds local extension paths.
An entry prefixed with `-` is excluded. Two entries are currently excluded:

- `-extensions/web-search/index.ts`
- `-extensions/ask-user-question.ts`

The leading `-` is documented only for package manifest filters. For the global
`extensions` array the docs say no more than "local extension file paths or
directories". Treat the exclusion behaviour here as observed, not guaranteed.

## Subagents

Two separate sets of agent definitions exist. They are NOT the same files.

- `agent/agents/` — `planner.md`, `reviewer.md`, `scout.md`, `worker.md`. This
  is the set pi loads at user scope. `planner`, `reviewer`, and `scout` declare
  a `tools:` list. `worker` does not.
- `agent/extensions/subagent/agents/` — the same four names, but each adds a
  `model:` line (`claude-sonnet-4-5`, and `claude-haiku-4-5` for `scout`).
- `agent/extensions/subagent/prompts/` — `implement.md`,
  `implement-and-review.md`, `scout-and-plan.md`.

## Validating changes

There is no test suite, and no static typecheck can run.

- `pnpm exec tsc --noEmit` does NOT work. TypeScript is not installed, and
  `agent/extensions/` has no `package.json` and no `tsconfig.json`. The only
  `package.json` under `agent/` is `agent/npm/package.json`, and it declares no
  scripts and no devDependencies.
- The real check is runtime. pi loads the TypeScript source directly, so a
  syntax error appears as a failed extension load.

Reload pi with `/reload` to load a changed extension, or restart.

To verify behaviour end to end, run a headless session and read the tool calls:

```
pi -p --no-session --mode json "<prompt>"
```

`--mode json` streams `tool_execution_start` events, so you can see exactly
which tool the agent chose. That is how the CodeGraph loader race below was
found and confirmed. Add `-e <path>` to load a throwaway probe extension.
Delete any probe when you are done.

## CodeGraph

`.codegraph/codegraph.db` is a machine-local index. It covers more than
TypeScript: the CLI also indexes the Python and the XML/YAML under
`agent/skills/`.

The eight `codegraph_*` tools are INACTIVE by default. They reach the provider
only after `codegraph_load` runs, and `codegraph-enhanced` adds
`codegraph_load` only when the working folder has an index. Prose that names
`codegraph_search` and its siblings does not work on its own: the model cannot
call a tool it was never given. Put the instruction where the tool list can
back it up.

`codegraph-enhanced` carries a `LOCAL PATCH`. The loader is set from a
synchronous check for `.codegraph/codegraph.db` in the working folder or an
ancestor, because the upstream version raced the async status call and stayed
invisible on the first turn. The async result remains authoritative. Preserve
the patch and its comment.

After a structural change (a renamed or moved symbol, a new file), re-index
before you rely on the graph:

```
codegraph sync
```

JSON and `.md` files are not in the graph. Read them directly.

## Config and state files

- `agent/settings.json` — provider, model, theme, `packages`, `extensions`.
  String values may use `${ENV_VAR}` expansion for secrets.
- `agent/APPEND_SYSTEM.md` — appended to every system prompt.
- `agent/pretty-tui.json` — `pi-pretty-tui` config.
- `agent/web-search.json` — `web-search` config. Untracked and NOT in
  `.gitignore`, so it can be committed by accident. Do not commit it.
- `agent/npm/` — npm install root for the `packages` entries.

Gitignored machine-local state: `agent/auth.json`, `agent/sessions/`,
`agent/models-store.json`, `agent/bin/`, `agent/web-search-cache/`,
`agent/trust.json`, `agent/cache/`.

No extension keeps a `config.json` today. If one needs hand-edited config,
resolve it with `join(getAgentDir(), "extensions", "<name>", "config.json")`.
Do not use `__dirname`: it points into `node_modules/` for an npm install,
differs for a project-local copy, and ignores `PI_CODING_AGENT_DIR`. Put
generated dynamic state at `<agentDir>/<name>.json` instead, so it cannot
overwrite hand-edited config, and add that path to `.gitignore`.

## Git conventions

Conventional Commits. Lowercase subject, no body unless context is genuinely
needed:

```
feat: add todo tool and /todos command
docs: add README
chore: release 0.1.0
```

Add a scope for an extension-scoped change, for example
`fix(codegraph-enhanced): set the loader from a synchronous index check`.

- Do not commit generated files, `.codegraph/codegraph.db`, `agent/auth.json`,
  `agent/models-store.json`, `agent/trust.json`, `agent/sessions/`, or any
  token or credential. The `.gitignore` already covers most of these.
- `agent/npm/node_modules/` and the `node_modules/` under `browser/` and
  `web-fetch/` are install output. Never edit them by hand.

## This file

pi discovers `AGENTS.md` at the repository root and injects it into every
session that works here. Keep it lean and factual. Do not add build steps,
scripts, or config files that do not exist.

`agent/APPEND_SYSTEM.md` requires reading this file during Planning Stage 1.
Several skills under `agent/skills/` also point here. If you add a standing
rule or invariant, put it in this file so scout, worker, and reviewer pick it
up.

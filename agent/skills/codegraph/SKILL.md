---
name: codegraph
description: "CodeGraph is a code-intelligence knowledge graph. ALWAYS use this skill — and load it FIRST — whenever you need to search, look up, or locate ANYTHING in a codebase: a file, function, method, class, symbol, definition, reference, or code path. Also use it to understand project structure, file layout, and naming/conventions. It fully replaces grep, rg, find, tree, ls, and cat for codebase exploration — do NOT reach for those tools before trying CodeGraph."
---

# CodeGraph Skill

CodeGraph is a code-intelligence & knowledge graph for any codebase. It builds an index of symbols, definitions, and call relationships, then lets you query that graph directly — no recursive `grep`/`find`/`cat` needed.

Use this skill when the user asks structural, architectural, or relational questions about the codebase: call chains, who calls whom, change impact / blast radius, finding declarations, affected tests, exploring how components interact, or mapping the project's file structure and understanding its conventions (naming, layout, symbol organization).

## Usage Instructions

Run CodeGraph CLI commands directly via the `bash` tool. Most query commands take a symbol name or natural-language query and return precise, indexed results in a single turn — far faster and more accurate than scanning files by hand.

> The CLI is the same engine that powers the `codegraph_explore` and `codegraph_node` MCP tools. `codegraph explore` and `codegraph node` produce identical output to those tools.

## Index Lifecycle

CodeGraph needs an index before queries return results. In a project with a `.codegraph/` directory the index already exists; otherwise it can be (re)built:

```bash
codegraph init [path]        # Initialize + build initial index
codegraph index [path]       # Rebuild the full index from scratch (same as fresh init)
codegraph sync [path]        # Sync changes since last index (incremental)
codegraph status [path]      # Show index status & statistics
codegraph uninit [path]      # Remove .codegraph/ from a project
codegraph unlock [path]      # Remove a stale lock file blocking indexing
```

## Query Commands

### 1. Architectural Exploration
Ask a natural-language question and get the relevant symbols' source plus call paths in one shot:

```bash
codegraph explore "How does authentication flow to the request handler?"
```

### 2. Inspect a Single Symbol or File
`node` shows one symbol's source plus its caller/callee trail. Given a file path (or no name), it reads the file with line numbers and lists its dependents:

```bash
codegraph node <symbol>      # source + caller/callee trail
codegraph node <path>        # file with line numbers + dependents
```

### 3. Trace Callers & Callees
Find what triggers a function, or everything a function calls:

```bash
codegraph callers <symbol>   # all functions/methods that call a symbol
codegraph callees <symbol>   # all functions/methods a symbol calls
```

### 4. Change Impact Analysis (Blast Radius)
See what code is affected by modifying a specific class or interface:

```bash
codegraph impact <symbol>
```

### 5. Find Affected Tests
Given changed source files, find the test files that cover them:

```bash
codegraph affected [files...]
```

### 6. Search & Locate Symbols
Find definitions, symbols, and files without reading whole modules. The command is `query` (not `search`):

```bash
codegraph query <search>
```

### 7. Project Structure & Conventions
Understand how the project is laid out and the conventions it follows, straight from the index — no manual tree walking needed.

#### 7a. View the file structure
`files` renders the project layout as the index sees it. Use the format/filter options to switch between an overview and a focused cut:

```bash
codegraph files                          # tree view (default), with language & symbol counts
codegraph files --format flat            # flat list of every indexed file
codegraph files --format grouped         # group files by language/type — great for spotting conventions
codegraph files --filter src/api         # only files under a given directory
codegraph files --pattern "**/*.test.*"  # only files matching a glob (e.g. test layout)
codegraph files --max-depth 2            # shallow tree for a quick orientation
codegraph files --no-metadata            # just the structure, no per-file counts
codegraph files -j                       # JSON output for downstream parsing
```

Use `--format grouped` to infer conventions at a glance: where source lives, where tests live, how config is split, which languages coexist, and how files are named per type.

#### 7b. Discover naming & symbol conventions
`query` with a `--kind` filter reveals how the project names and organizes each symbol category — useful for matching existing patterns when adding code:

```bash
codegraph query --kind function --limit 30   # all functions, see naming/style conventions
codegraph query --kind class     --limit 30  # class declaration patterns
codegraph query --kind interface --limit 30  # interface/type conventions
codegraph query "Controller"  --limit 30      # find a naming pattern across the codebase
codegraph query "handle"     --limit 30      # see how handlers are named/wired
```

#### 7c. Structural statistics
`status` reports what the index knows about the project — file counts by language, symbol counts, and index health — a fast way to size up conventions and coverage before diving in:

```bash
codegraph status        # human-readable summary
codegraph status -j     # JSON for scripting
```

**When to use which:** reach for `files` to map the layout, `query --kind` to learn how symbols are named and grouped, and `status` to get the high-level profile of the codebase.

## Management Commands

```bash
codegraph daemon              # Manage running background daemons (pick one to stop)
codegraph install             # Install codegraph MCP server into agents (Claude Code, Cursor, Codex CLI, opencode, Hermes Agent)
codegraph uninstall           # Remove codegraph from agents
codegraph upgrade [version]   # Update CodeGraph (or pin a specific version)
codegraph version             # Print installed version (also -v / --version)
codegraph telemetry <action>  # Show/change anonymous usage telemetry (status|on|off)
codegraph help [command]      # Help for a specific command
```

## Rules

- NEVER default to recursive file reads (`cat`, `less`) or text searches (`grep`, `find`) for tracking code dependencies or symbol locations. Use CodeGraph queries instead.
- Prefer `codegraph node` / `callers` / `callees` / `impact` for precise, one-shot relational context.
- Use `codegraph explore` for open-ended "how does X work" questions.
- Use `codegraph files`, `query --kind`, and `status` to understand project structure, naming, and conventions instead of `ls`/`tree`/`find`/`grep`.
- Use `codegraph affected` when the user wants to know which tests to run after a change.
- If queries return no results, check `codegraph status` and run `codegraph sync` (or `codegraph index`) to refresh the index.

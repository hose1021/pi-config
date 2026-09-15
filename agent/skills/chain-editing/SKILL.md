---
name: chain-editing
description: Edit agent-chain.yaml chains, steps, prompts, verdicts, returns, and approval gates.
disable-model-invocation: true
---

# Chain editing

Edits `agent/agents/agent-chain.yaml` — named step pipelines dispatched through native task. A project override at `.omp/agents/agent-chain.yaml` wins when present; check it first and edit that one instead.

## Shape

```yaml
<chain-name>:
  description: "What it is for."
  steps:
    - id: plan              # optional; defaults to step-N. Unique, starts with a letter.
      agent: planner        # must exist in agent/agents/
      prompt: "Do X with:\n\n$INPUT"
      approval: true        # optional: pause before every visit until /chain-approve
      verdict: true         # optional: step must return {verdict: PASS|FAIL, summary}
      on_error:             # optional: bounded return on failure
        goto: plan          # id of this or an earlier step only
        max_returns: 2      # positive integer; lifetime budget of the failing step
```

- Placeholders expand literally once: `$ORIGINAL` (initial task), `$INPUT` (previous step output; first step: the task), `$ERROR` (live repair feedback), `$STEP:<id>` (an earlier step's output; the id must exist and precede this step).
- Unknown fields at chain, step, and on_error levels are rejected before any dispatch.
- Verdict steps get a strict output schema. PASS summary becomes the next `$INPUT`; FAIL summary becomes `$ERROR` and triggers `on_error`.
- Without `on_error`, a failure stops the chain. Cancellation never retries. Returns do not undo file edits, commits, or external actions.

## Runtime contract (already enforced; do not restate it in prompts)

- `run_chain` or `/run-chain <prompt>` prepares a run. The model dispatches each step via native task with the exact name from `chain_status`, waits for the completed result, then calls `chain_status` again for the next step or return.
- Approval steps pause for the user: `/chain-approve` or `/chain-stop`. The model cannot approve.
- `/chain-monitor` shows the private localhost monitor URL. Run reports land in `.omp/chain-runs/<run>.{json,html}` and stay private.
- A killed or switched session leaves `.omp/chain-runs/<run>.state.json`. `/chain-resume` reloads the newest unfinished run and pauses it for `/chain-approve`, because the step that was in flight may have already changed files. A chain edited since the run started cannot resume.
- Unlike the reports, the state file holds every completed step's full output. It is written 0600 under a 0700 directory; keep `.omp/` out of commits.
- A brief of at most 30 lines and 1200 characters stays in the confirm dialog. A denser one is posted as an excerpt, cut to 200 characters per line, and the dialog offers Approve, Read full brief (scrollable), or Stop.
- A step runs on its agent's model: `task.agentModelOverrides[<agent>]`, then the agent frontmatter `model`, then the parent session's model. Chain YAML carries no model field; the task wire schema has none, so per-step models are expressed by pointing the step at an agent that resolves the model you want.

## Operations

- Add chain: append a new top-level `<name>:` block at file end.
- Add step: insert an `- id:` / `agent:` / `prompt:` item at the right position in `steps:`.
- Update: edit `description`, `prompt`, or the optional controls in place; keep placeholders intact.
- Remove: delete the step item or the whole chain block. Never leave a chain with zero steps.

## Rules

- Never edit the header comment; it documents the runtime contract.
- Multi-line prompts use `\n` escapes, as in existing chains.
- Keep prompts self-contained: each step sees only `$ORIGINAL`, `$INPUT`, `$ERROR`, and `$STEP:<id>` for an earlier step.
- Verify: `bun test agent/tests/agent-chain-state.test.ts agent/tests/agent-chain.test.ts` from `~/.omp`.

## Common mistakes

- Referencing a nonexistent agent, or a `goto` that is missing or later than the failing step: config rejected.
- Expecting words like FAIL in ordinary prose to trigger a return: verdicts are structured objects, not text scans.
- Editing the profile file while a project override exists: edits silently ignored.

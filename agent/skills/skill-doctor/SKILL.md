---
name: skill-doctor
description: Audit loaded skills — list every skill, flag unused ones, estimate token cost. Use when the user asks which skills are loaded, what skills cost, or says skill-doctor.
---

# Skill Doctor

Reports the three things it promises: loaded skills, unused ones, token cost.

## Run

```bash
python3 ~/.omp/agent/skills/skill-doctor/scripts/doctor.py
python3 ~/.omp/agent/skills/skill-doctor/scripts/doctor.py --session 01a078e1
python3 ~/.omp/agent/skills/skill-doctor/scripts/doctor.py --all
python3 ~/.omp/agent/skills/skill-doctor/scripts/doctor.py --json
python3 ~/.omp/agent/skills/skill-doctor/scripts/doctor.py --all --html [path]
```

Flags: `--session ID` (prefix, default: latest session), `--cwd SUBSTR`,
`--all` (scan every session), `--json`, `--html [path]` (dashboard with grade,
bars, findings, suggested changes; default path `.../skill-doctor/report.html`).

## How it works

- Loaded = every `*/SKILL.md` under `~/.omp/agent/skills` plus
  `customDirectories` from `~/.omp/agent/config.yml`, minus `ignoredSkills`.
- Used = a `read` tool call with `skill://<name>` or `<name>/SKILL.md` (prose mentions don't count).
- Tokens ~= chars/4 for description (per-turn cost) and full body (on-load cost).

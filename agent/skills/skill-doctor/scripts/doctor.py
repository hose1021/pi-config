from __future__ import annotations
import argparse
import json
import os
import re
import sys
from html import escape
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
OMP = HOME / ".omp"
DEFAULT_ROOTS = [OMP / "agent" / "skills"]
SESSIONS_ROOT = OMP / "agent" / "sessions"
CONFIG = OMP / "agent" / "config.yml"


def tok(s: str) -> int:
    return len(s) // 4


def parse_frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---\n?", text, re.S)
    out: dict = {}
    if not m:
        return out
    for line in m.group(1).splitlines():
        mm = re.match(r"(\w[\w-]*):\s*(.*)", line)
        if mm:
            out[mm.group(1)] = mm.group(2).strip()
    return out


def config_lists() -> tuple[list[str], list[str]]:
    """Minimal YAML parse: customDirectories + ignoredSkills only."""
    extra, ignored = [], []
    try:
        lines = CONFIG.read_text().splitlines()
    except OSError:
        return extra, ignored
    cur = None
    for line in lines:
        s = line.strip()
        if s.startswith("customDirectories:"):
            cur = "extra"
            continue
        if s.startswith("ignoredSkills:"):
            cur = "ignored"
            continue
        if s.startswith("- ") and cur:
            (extra if cur == "extra" else ignored).append(s[2:].strip())
        elif s and not s.startswith("#") and not s.startswith("-"):
            if not line.startswith((" ", "\t")):
                cur = None
    return extra, ignored


def discover_skills() -> list[dict]:
    extra, ignored = config_lists()
    roots = list(DEFAULT_ROOTS) + [Path(p).expanduser() for p in extra]
    seen: dict[str, dict] = {}
    for root in roots:
        if not root.is_dir():
            continue
        for skill_md in sorted(root.glob("*/SKILL.md")):
            try:
                text = skill_md.read_text()
            except OSError:
                continue
            fm = parse_frontmatter(text)
            name = fm.get("name", skill_md.parent.name)
            if name in ignored or name in seen:
                continue
            desc = fm.get("description", "")
            seen[name] = {
                "name": name,
                "path": str(skill_md),
                "description": desc,
                "desc_tok": tok(desc),
                "full_tok": tok(text),
                "bytes": len(text.encode()),
            }
    return sorted(seen.values(), key=lambda s: s["name"])


def find_session_files(session: str | None, cwd: str | None) -> list[Path]:
    files = [p for p in SESSIONS_ROOT.rglob("*.jsonl") if p.is_file()]
    if session:
        files = [p for p in files if session in p.name]
    elif cwd:
        keep = []
        for p in files:
            try:
                head = p.read_text()[:4000]
            except OSError:
                continue
            if cwd in head:
                keep.append(p)
        files = keep
    else:
        files = sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)[:1]
    return files


def read_paths(record: dict) -> list[str]:
    """Extract read-tool paths from a session record (calls only, not prose)."""
    out = []
    try:
        if record.get("type") == "message":
            content = (record.get("message") or {}).get("content") or []
            for item in content:
                if isinstance(item, dict) and item.get("name") == "read":
                    p = (item.get("arguments") or {}).get("path")
                    if p:
                        out.append(p)
        elif record.get("type") == "custom":
            data = record.get("data") or {}
            if data.get("toolName") == "read":
                p = (data.get("args") or {}).get("path")
                if p:
                    out.append(p)
    except (AttributeError, TypeError):
        pass
    return out


def path_to_skill(path: str) -> str | None:
    if path.startswith("skill://"):
        return path[len("skill://"):].split("/")[0] or None
    m = re.search(r"/([^/]+)/SKILL\.md", path)
    return m.group(1) if m else None


def scan_usage(files: list[Path], names: list[str]) -> dict[str, bool]:
    known = set(names)
    used = {n: False for n in names}
    for f in files:
        try:
            fh = open(f)
        except OSError:
            continue
        with fh:
            for line in fh:
                if "SKILL.md" not in line and "skill://" not in line:
                    continue
                try:
                    record = json.loads(line)
                except (ValueError, TypeError):
                    continue
                for p in read_paths(record):
                    n = path_to_skill(p)
                    if n in known:
                        used[n] = True
        if all(used.values()):
            break
    return used


def session_error_rate(files: list[Path]) -> tuple[int, int, list[tuple[str, int]]]:
    """Return (scored, clean, worst): sessions scanned, without errors, top error sessions."""
    scored, clean = 0, 0
    errs: dict[str, int] = {}
    for f in files:
        try:
            fh = open(f)
        except OSError:
            continue
        with fh:
            ident, bad, sid, n = False, False, f.stem[-12:], 0
            for line in fh:
                if '"toolResult"' not in line and '"session"' not in line:
                    continue
                try:
                    r = json.loads(line)
                except (ValueError, TypeError):
                    continue
                t = r.get("type")
                if t == "session":
                    ident = True
                    sid = str(r.get("id", sid))[:8]
                elif (t == "message" and (r.get("message") or {}).get("role") == "toolResult"
                        and (r.get("message") or {}).get("isError")):
                    bad, n = True, n + 1
            if ident:
                scored += 1
                if not bad:
                    clean += 1
                else:
                    errs[sid] = n
    worst = sorted(errs.items(), key=lambda kv: kv[1], reverse=True)[:3]
    return scored, clean, worst


def grade(overall: int) -> str:
    letter = "A" if overall >= 90 else "B" if overall >= 80 else "C" if overall >= 70 \
        else "D" if overall >= 60 else "F"
    return letter if letter == "F" else letter + ("+" if overall % 10 >= 7 else "")


def frontmatter_lines(skill_path: str, limit: int = 5) -> list[str]:
    try:
        text = Path(skill_path).read_text()
    except OSError:
        return []
    m = re.match(r"^---\n(.*?)\n---\n?", text, re.S)
    if not m:
        return []
    return m.group(0).splitlines()[:limit]


def short_path(p: str, keep: int = 42) -> str:
    return "…" + p[-keep:] if len(p) > keep else p


def suggestion_block(i: int, r: dict, scope: str) -> str:
    name = r["name"]
    sp = short_path(r["path"])
    dtok = r["desc_tok"]
    ftok = r["full_tok"]
    fm_lines = frontmatter_lines(r["path"])
    add = '<span class="dl-add">+ disable-model-invocation: true</span>'
    if fm_lines and fm_lines[-1].strip() == "---":
        fm_lines = fm_lines[:-1] + [add, "---"]
    else:
        fm_lines = fm_lines + [add]
    ctx = "".join("\n  " + (ln if ln.startswith("<span") else escape(ln)) for ln in fm_lines)
    parts = [
        '<div class="sugg">' + str(i) + '. <span class="pill">' + escape(name) + "</span>",
        " - Convert to user-invoked: add <code>disable-model-invocation: true</code>",
        " to frontmatter so it loads only when typed by name.",
        " Saves ~" + str(dtok) + " tok/turn.",
        '<p class="ev">Evidence: zero detected reads in ' + escape(scope) + ";",
        " description ~" + str(dtok) + " tok/turn, body ~" + str(ftok) + " tok;",
        " file <code>" + escape(sp) + "</code>.</p>",
        '<div class="diffhead">' + escape(sp) + " (proposed edit)",
        ' <span class="add">+1</span></div>',
        '<pre class="diff">' + ctx + "</pre></div>",
    ]
    return "".join(parts)


def render_html(path: Path, scope: str, rows: list[dict], scored: int, clean: int,
                worst: list[tuple[str, int]] | None = None) -> None:
    total = len(rows)
    used_rows = [r for r in rows if r["used"]]
    unused = [r for r in rows if not r["used"]]
    coverage = round(100 * len(used_rows) / total) if total else 0
    desc_total = sum(r["desc_tok"] for r in rows)
    efficiency = round(100 * sum(r["desc_tok"] for r in used_rows) / desc_total) if desc_total else 0
    quality = round(100 * clean / scored) if scored else 100
    overall = round(0.5 * coverage + 0.3 * efficiency + 0.2 * quality)
    g = grade(overall)
    unused_names = ", ".join(r["name"] for r in sorted(unused, key=lambda r: r["full_tok"], reverse=True)[:12])
    big = max(unused, key=lambda r: r["full_tok"], default=None)
    findings = [
        f"Dead weight is the majority. {total} skills are installed and {len(used_rows)} fired in {scope}. "
        f"Zero detected use: {unused_names}{' …' if len(unused) > 12 else ''}.",
    ]
    if big:
        findings.append(f"Biggest offender is {big['name']} (~{big['full_tok']} tok body, "
                        f"~{big['desc_tok']} tok/turn description) with no detected use — "
                        "top candidate to disable or convert to user-invoked.")
    findings.append(f"Always-loaded descriptions cost ~{desc_total} tok/turn; "
                    f"~{desc_total - sum(r['desc_tok'] for r in used_rows)} of that is unused skills.")
    if scored:
        findings.append(f"Session health: {clean}/{scored} scored sessions have zero tool errors.")
    for sid, n in (worst or []):
        findings.append(f"Tool errors concentrate in session {sid} ({n} error results) - "
                        "check it with show_session.py before blaming skills.")
    top_unused = sorted(unused, key=lambda r: r["full_tok"], reverse=True)[:3]
    sugg_html = "".join(suggestion_block(i + 1, r, scope) for i, r in enumerate(top_unused))
    bars = [("efficiency", efficiency), ("code quality", quality), ("skill coverage", coverage)]
    bar_html = "".join(
        f'<div class="row"><span>{n}</span><b>{v}</b></div>'
        f'<div class="bar"><i style="width:{v}%"></i></div>' for n, v in bars)
    find_html = "".join(f"<li>{f}</li>" for f in findings)
    skill_rows = "".join(
        f"<tr class=\"{'on' if r['used'] else 'off'}\"><td>{r['name']}</td>"
        f"<td>{'used' if r['used'] else 'unused'}</td>"
        f"<td>{r['desc_tok']}</td><td>{r['full_tok']}</td></tr>" for r in rows)
    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>skill-doctor report</title>
<style>
:root{{color-scheme:dark}}*{{box-sizing:border-box;margin:0}}
body{{background:#0b0b12;color:#e8e8ef;font:14px/1.6 ui-monospace,SFMono-Regular,Menlo,monospace;
background-image:radial-gradient(#1c1c28 1px,transparent 1px);background-size:22px 22px;padding:32px 16px}}
.card{{max-width:900px;margin:0 auto 24px;background:#14141d;border:1px solid #2a2a3a;border-radius:10px;overflow:hidden}}
.top{{display:flex;gap:32px;padding:32px;align-items:center;flex-wrap:wrap}}
.grade{{font-size:96px;font-weight:800;color:#9d8cff;line-height:1}}
.overall{{color:#8a8a9a;font-size:12px;letter-spacing:2px;margin-top:8px}}
.bars{{flex:1;min-width:280px}}.row{{display:flex;justify-content:space-between;margin:14px 0 6px}}
.bar{{height:10px;background:#2a2a35;border-radius:2px}}.bar i{{display:block;height:100%;background:#9d8cff;border-radius:2px}}
.stats{{display:grid;grid-template-columns:repeat(3,1fr);border-top:1px solid #2a2a3a}}
.stats div{{padding:24px;border-left:1px solid #2a2a3a}}.stats div:first-child{{border-left:0}}
.stats b{{font-size:40px;display:block}}.stats span{{color:#9a9aa8;font-size:13px}}
h2{{max-width:900px;margin:8px auto 12px;font-size:24px}}ul.find{{max-width:900px;margin:0 auto;list-style:none}}
ul.find li{{margin:0 0 16px;padding-left:20px;position:relative}}ul.find li::before{{content:"•";position:absolute;left:0;color:#9d8cff}}
table{{max-width:900px;width:calc(100% - 0px);margin:24px auto;border-collapse:collapse;font-size:13px}}
th,td{{text-align:left;padding:6px 10px;border-bottom:1px solid #23232f}}th{{color:#8a8a9a;font-weight:400}}
tr.off td:first-child{{color:#b9b9c9}}tr.on td:first-child{{color:#9d8cff}}.foot{{max-width:900px;margin:16px auto;color:#71717f;font-size:12px}}
.sugg{{max-width:900px;margin:0 auto 20px}}.pill{{background:#3a2b2b;color:#ffb4b4;padding:2px 8px;border-radius:4px}}
.sugg code{{background:#23232f;padding:1px 5px;border-radius:3px}}
.ev{{color:#8a8a9a;margin:8px 0;font-size:13px}}.diffhead{{color:#9d8cff;font-size:12px;margin:8px 0 4px}}
.add{{color:#4ade80}}.diff{{background:#000;border:1px solid #2a2a3a;border-radius:6px;padding:12px;overflow-x:auto;font-size:12px}}
.dl-add{{color:#4ade80;display:block;background:rgba(74,222,128,.08)}}
@media(max-width:640px){{.stats{{grid-template-columns:1fr}}.stats div{{border-left:0;border-top:1px solid #2a2a3a}}}}
</style></head><body>
<div class="card"><div class="top"><div><div class="grade">{g}</div>
<div class="overall">OVERALL {overall}</div></div><div class="bars">{bar_html}</div></div>
<div class="stats"><div><b>{scored}</b><span>conversations scored</span></div>
<div><b>{total}</b><span>skills installed</span></div>
<div><b>{len(used_rows)}</b><span>skills used</span></div></div></div>
<h2>Findings</h2><ul class="find">{find_html}</ul>
<h2>Suggested skill changes</h2>{sugg_html}
<table><tr><th>skill</th><th>status</th><th>desc tok</th><th>full tok</th></tr>{skill_rows}</table>
<p class="foot">scope: {scope} · tokens ~= chars/4 · overall = 0.5·coverage + 0.3·efficiency + 0.2·quality ·
efficiency = used-description share · quality = sessions without tool errors</p>
</body></html>"""
    path.write_text(html)


def main() -> None:
    ap = argparse.ArgumentParser(description="skill-doctor: loaded / unused / token cost")
    ap.add_argument("--session", default=None, help="session id prefix (default: latest session)")
    ap.add_argument("--cwd", default=None, help="filter sessions by cwd substring")
    ap.add_argument("--all", action="store_true", help="scan all sessions instead of latest")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--html", nargs="?", const=str(OMP / "agent" / "skills" / "skill-doctor" / "report.html"),
                    default=None, help="write HTML dashboard (default path if bare flag)")
    a = ap.parse_args()

    skills = discover_skills()
    names = [s["name"] for s in skills]
    files = (list(SESSIONS_ROOT.rglob("*.jsonl")) if a.all
             else find_session_files(a.session, a.cwd))
    used = scan_usage(files, names)

    rows = [{**s, "used": used[s["name"]]} for s in skills]
    rows.sort(key=lambda r: r["full_tok"], reverse=True)
    scope = f"{len(files)} session(s)" if a.all or a.session or a.cwd else "latest session"

    if a.html:
        scored, clean, worst = session_error_rate(files)
        out = Path(a.html).expanduser()
        render_html(out, scope, rows, scored, clean, worst)
        print(f"report: {out}")
        return

    if a.json:
        print(json.dumps({"scope": scope, "skills": rows}, indent=1))
        return

    unused = [r for r in rows if not r["used"]]
    print(f"# skill-doctor ({scope}, {len(rows)} skills, tokens ~= chars/4)\n")
    print("| skill | used | desc tok | full tok | path |")
    print("|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['name']} | {'yes' if r['used'] else 'no'} | {r['desc_tok']} "
              f"| {r['full_tok']} | {r['path']} |")
    print(f"\nUnused: {len(unused)}/{len(rows)}: " + (", ".join(r["name"] for r in unused) or "none"))
    print(f"Always-loaded cost (all descriptions): ~{sum(r['desc_tok'] for r in rows)} tok/turn")
    print(f"If all bodies loaded: ~{sum(r['full_tok'] for r in rows)} tok")

if __name__ == "__main__":
    sys.exit(main())

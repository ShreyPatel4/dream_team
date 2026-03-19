"""
pm_health_sweep.py — Agent 02 (PM) Health Check Sweep

Triggers:
  (a) Chief explicit call: orchestrator calls sweep()
  (b) Cron every 5 min: background thread auto-fires
  (c) Every Slack message received: telemetry hook calls sweep()

Sweep logic:
  1. Read all dumps in context-dumps/
  2. Diff timestamps against stale_threshold_minutes per agent
  3. Read notebooks/<agent-name>/progress.md for each active agent
  4. Diff against kanban/state.json (Trello local cache)
  5. Post standup to Slack #standup
  6. Write PM context dump to context-dumps/pm-02/YYYY-MM-DD/
"""

import os
import re
import json
import glob
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta

PROJECT_ROOT = Path(os.path.dirname(os.path.abspath(__file__)))
DUMP_DIR = PROJECT_ROOT / "context-dumps"
NOTEBOOK_DIR = PROJECT_ROOT / "notebooks"
KANBAN_FILE = PROJECT_ROOT / "kanban" / "state.json"
SKILLS_DIR = PROJECT_ROOT / "global-skills"

# ─── Default stale thresholds (overridden by SKILL.md frontmatter) ───
DEFAULT_THRESHOLDS = {
    "08": 2, "02": 5, "12": 2, "00": 10, "11": 10,
    "01": 10, "03": 10, "04": 10, "05": 10, "06": 10,
    "07d": 10, "09": 10, "10": 10,
    "01w": 15, "02w": 15, "03w": 15,
    "04w": 15, "04w2": 15,
    "05w": 15, "05w2": 15, "05w3": 15,
    "06w": 15, "06w2": 15, "06w3": 15,
    "07a": 15, "07b": 15, "07c": 15, "07w": 15,
    "09w": 15, "10w": 15, "10w2": 15,
}


def _parse_stale_threshold(agent_id: str) -> int:
    """Read stale_threshold_minutes from agent's SKILL.md frontmatter."""
    skill_dirs = list(SKILLS_DIR.glob(f"*{agent_id}*/SKILL.md"))
    for skill_path in skill_dirs:
        try:
            text = skill_path.read_text()
            match = re.search(r'stale_threshold_minutes:\s*(\d+)', text)
            if match:
                return int(match.group(1))
        except Exception:
            pass
    return DEFAULT_THRESHOLDS.get(agent_id, 15)


def _get_latest_dump(agent_slug: str) -> tuple:
    """Find the most recent dump file for an agent slug. Returns (path, timestamp)."""
    agent_dir = DUMP_DIR / agent_slug
    if not agent_dir.exists():
        return None, None

    latest_file = None
    latest_mtime = 0
    for md_file in agent_dir.rglob("*.md"):
        mtime = md_file.stat().st_mtime
        if mtime > latest_mtime:
            latest_mtime = mtime
            latest_file = md_file

    if latest_file:
        return str(latest_file), datetime.fromtimestamp(latest_mtime)
    return None, None


def _read_notebook_progress(agent_id: str) -> str:
    """Read the progress.md from an agent's notebook."""
    for pattern in [f"agent-{agent_id}", f"agent-{agent_id}"]:
        progress_path = NOTEBOOK_DIR / pattern / "progress.md"
        if progress_path.exists():
            try:
                return progress_path.read_text().strip()[:500]
            except Exception:
                pass
    return ""


def _read_kanban_state() -> dict:
    """Read the local Kanban state cache."""
    try:
        if KANBAN_FILE.exists():
            return json.loads(KANBAN_FILE.read_text())
    except Exception:
        pass
    return {"in_progress": [], "blocked": [], "qa": [], "done": []}


def sweep(project: str = "default", post_to_slack: bool = True) -> dict:
    """
    Full PM health check sweep.

    Returns a dict with sweep results for consumption by the caller
    or for writing to the PM's context dump.
    """
    now = datetime.now()
    kanban = _read_kanban_state()

    # Map agent IDs to their dump directory slugs
    from context_dump_writer import AGENT_META
    agent_statuses = []
    stale_agents = []
    active_count = 0

    for agent_id, meta in AGENT_META.items():
        slug = meta["slug"]
        threshold = _parse_stale_threshold(agent_id)

        dump_path, dump_time = _get_latest_dump(slug)
        progress = _read_notebook_progress(agent_id)

        if dump_time:
            delta = (now - dump_time).total_seconds() / 60
            is_stale = delta > threshold
            last_dump_str = f"{int(delta)}m ago"
            active_count += 1
        else:
            is_stale = False
            last_dump_str = "never"
            delta = 0

        status_entry = {
            "id": agent_id,
            "name": meta["name"],
            "status": "STALE" if is_stale else ("ACTIVE" if dump_time else "IDLE"),
            "last_dump": last_dump_str,
            "stale": "YES" if is_stale else "NO",
            "threshold_min": threshold,
            "delta_min": round(delta, 1),
            "has_progress": bool(progress),
        }
        agent_statuses.append(status_entry)

        if is_stale:
            stale_agents.append(f"{meta['name']} ({agent_id}): {int(delta)}m > {threshold}m")

    # ── Kanban diff ──
    in_progress = kanban.get("in_progress", [])
    blocked = kanban.get("blocked", [])
    in_qa = kanban.get("qa", [])
    done = kanban.get("done", [])

    sweep_result = {
        "timestamp": now.isoformat(),
        "project": project,
        "agent_statuses": agent_statuses,
        "stale_agents": stale_agents,
        "active_count": active_count,
        "total_agents": len(AGENT_META),
        "sprint_health": {
            "in_progress": len(in_progress),
            "blocked": len(blocked),
            "in_qa": len(in_qa),
            "done": len(done),
            "tasks_total": len(in_progress) + len(blocked) + len(in_qa) + len(done),
        },
        "kanban_drift": 0,
    }

    # ── Post standup to Slack ──
    if post_to_slack:
        _post_standup(sweep_result)

    # ── Write PM context dump ──
    _write_pm_dump(sweep_result, now, project)

    return sweep_result


def _post_standup(result: dict):
    """Post standup summary to Slack #standup."""
    health = result["sprint_health"]
    stale_count = len(result["stale_agents"])

    msg = (
        f"#standup: {health['in_progress']} in-flight, "
        f"{health['blocked']} blocked, {health['in_qa']} in QA"
    )
    if stale_count:
        msg += f" ⚠️ {stale_count} stale agent(s)"

    try:
        import subprocess
        subprocess.run([
            "python3", str(PROJECT_ROOT / "slack_worker.py"),
            "C0AM3R8GSU9",  # #standup channel
            "Agent 02 | Project Manager",
            ":clipboard:",
            msg
        ], timeout=10, capture_output=True)
    except Exception:
        pass  # Non-blocking — Slack is best-effort


def _write_pm_dump(result: dict, now: datetime, project: str):
    """Write PM's own context dump."""
    try:
        from context_dump_writer import dump
        dump.save(
            agent_id="02",
            agent_name="Project Manager",
            action_type="health_sweep",
            summary=f"Sweep: {result['active_count']} active, {len(result['stale_agents'])} stale",
            project=project,
            data={
                "status": "SWEEPING",
                "sprint_number": "current",
                "sprint_day": "?",
                "sprint_length": "?",
                "tasks_total": result["sprint_health"]["tasks_total"],
                "in_progress": result["sprint_health"]["in_progress"],
                "blocked": result["sprint_health"]["blocked"],
                "in_qa": result["sprint_health"]["in_qa"],
                "done": result["sprint_health"]["done"],
                "ip_agents": [],
                "blocker_details": [],
                "agent_statuses": result["agent_statuses"],
                "kanban_drift": result["kanban_drift"],
                "kanban_action": "none",
                "next_action": "Next sweep in 5 minutes",
            }
        )
    except Exception:
        pass


# ─── Cron Thread ───

_cron_thread = None
_cron_running = False


def start_cron(interval_seconds: int = 300, project: str = "default"):
    """Start background cron thread that fires sweep every `interval_seconds`."""
    global _cron_thread, _cron_running
    if _cron_running:
        return

    _cron_running = True

    def _loop():
        while _cron_running:
            try:
                sweep(project=project, post_to_slack=True)
            except Exception as e:
                print(f"[PM Sweep cron error] {e}")
            time.sleep(interval_seconds)

    _cron_thread = threading.Thread(target=_loop, daemon=True, name="pm-sweep-cron")
    _cron_thread.start()
    print(f"[PM Sweep] Cron started: every {interval_seconds}s")


def stop_cron():
    global _cron_running
    _cron_running = False


# ─── CLI entry point ───
if __name__ == "__main__":
    import sys
    project = sys.argv[1] if len(sys.argv) > 1 else "default"
    result = sweep(project=project, post_to_slack=False)
    print(json.dumps(result, indent=2, default=str))

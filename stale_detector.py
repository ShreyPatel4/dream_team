"""
stale_detector.py — Agent 12 (Alert Monitor) Stale Detection

Watches context-dumps/ for freshness. Polls every 60 seconds.
For each active agent:
  - Compare last dump timestamp to now
  - If delta > stale_threshold_minutes from SKILL.md → P1 alert
  - Post to Slack #alerts
  - Log to audit-log/YYYY-MM-DD.md

Usage:
    # Standalone
    python3 stale_detector.py

    # As a module
    from stale_detector import StaleDetector
    detector = StaleDetector()
    detector.start()
"""

import os
import re
import time
import threading
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(os.path.dirname(os.path.abspath(__file__)))
DUMP_DIR = PROJECT_ROOT / "context-dumps"
SKILLS_DIR = PROJECT_ROOT / "global-skills"
AUDIT_DIR = PROJECT_ROOT / "audit-log"

# ─── Agent directory slugs (must match context_dump_writer.py) ───
AGENT_SLUGS = {
    "08": "chief-08", "01": "po-01", "02": "pm-02", "03": "tl-03",
    "04": "de-04", "05": "swe-05", "06": "ops-06", "07d": "sec-07d",
    "09": "res-09", "10": "qa-10", "11": "git-11", "12": "mon-12",
    "00": "gov-00", "01w": "pa-01w", "02w": "sm-02w", "03w": "sa-03w",
    "04w": "de-04w", "04w2": "dq-04w2", "05w": "swe-05w",
    "05w2": "sys-05w2", "05w3": "fe-05w3", "06w": "devops-06w",
    "06w2": "mlops-06w2", "06w3": "gpu-06w3", "07a": "rt-07a",
    "07b": "comp-07b", "07c": "st-07c", "07w": "secauto-07w",
    "09w": "re-09w", "10w": "qa-10w", "10w2": "qauto-10w2",
}

AGENT_NAMES = {
    "08": "Chief Orchestrator", "01": "Product Owner", "02": "Project Manager",
    "03": "Tech Lead", "04": "Lead Data Eng", "05": "Lead SWE",
    "06": "Lead Ops", "07d": "CISO", "09": "Research Scientist",
    "10": "QA Lead", "11": "Git Guardian", "12": "Alert Monitor",
    "00": "Org Governance", "01w": "Product Analyst", "02w": "Scrum Master",
    "03w": "Solutions Architect", "04w": "Sr Data Engineer",
    "04w2": "Data Quality Eng", "05w": "Sr SWE Backend",
    "05w2": "SWE Systems", "05w3": "SWE Frontend",
    "06w": "DevOps Engineer", "06w2": "MLOps Engineer",
    "06w3": "GPU/CUDA Eng", "07a": "Red Team Analysts",
    "07b": "Compliance Eng", "07c": "Security Tester",
    "07w": "Security Automation", "09w": "Research Engineer",
    "10w": "QA Engineer", "10w2": "QA Automation",
}

DEFAULT_THRESHOLDS = {
    "08": 2, "02": 5, "12": 2, "00": 10, "11": 10,
    "01": 10, "03": 10, "04": 10, "05": 10, "06": 10,
    "07d": 10, "09": 10, "10": 10,
}


def _parse_stale_threshold(agent_id: str) -> int:
    """Read stale_threshold_minutes from SKILL.md frontmatter."""
    for skill_path in SKILLS_DIR.glob(f"*{agent_id}*/SKILL.md"):
        try:
            text = skill_path.read_text()
            match = re.search(r'stale_threshold_minutes:\s*(\d+)', text)
            if match:
                return int(match.group(1))
        except Exception:
            pass
    return DEFAULT_THRESHOLDS.get(agent_id, 15)


def _get_latest_dump_time(agent_slug: str) -> float:
    """Get the mtime of the most recent dump for an agent."""
    agent_dir = DUMP_DIR / agent_slug
    if not agent_dir.exists():
        return 0

    latest = 0
    for md_file in agent_dir.rglob("*.md"):
        mtime = md_file.stat().st_mtime
        if mtime > latest:
            latest = mtime
    return latest


def _write_audit_line(msg: str):
    """Append to today's audit log."""
    now = datetime.now()
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    log_file = AUDIT_DIR / f"{now.strftime('%Y-%m-%d')}.md"

    line = f"[{now.strftime('%H:%M:%S')}] Alert Monitor | stale_check | {msg}\n"
    with open(log_file, "a") as f:
        if log_file.stat().st_size == 0:
            f.write(f"# Audit Log — {now.strftime('%Y-%m-%d')}\n\n")
        f.write(line)


def _post_p1_alert(agent_id: str, agent_name: str, delta_min: float):
    """Post P1 alert to Slack #alerts."""
    msg = f"P1: {agent_name} ({agent_id}) stale for {int(delta_min)}m"
    try:
        import subprocess
        subprocess.run([
            "python3", str(PROJECT_ROOT / "slack_worker.py"),
            "C0AL9ER7LUF",  # #alerts channel
            "Agent 12 | Alert Monitor",
            ":rotating_light:",
            msg
        ], timeout=10, capture_output=True)
    except Exception:
        pass  # Non-blocking


class StaleDetector:
    def __init__(self, poll_interval: int = 60):
        self.poll_interval = poll_interval
        self._running = False
        self._thread = None
        self._alerted = set()  # Track already-alerted agents to avoid spam

    def check_once(self) -> list:
        """Run one staleness check across all agents. Returns list of stale agents."""
        now = time.time()
        stale = []
        alert_count = {"p0": 0, "p1": 0, "p2": 0}

        for agent_id, slug in AGENT_SLUGS.items():
            threshold = _parse_stale_threshold(agent_id)
            last_dump = _get_latest_dump_time(slug)

            if last_dump == 0:
                continue  # Agent never dumped — not active, skip

            delta_min = (now - last_dump) / 60.0

            if delta_min > threshold:
                name = AGENT_NAMES.get(agent_id, f"Agent {agent_id}")
                stale.append({
                    "agent_id": agent_id,
                    "agent_name": name,
                    "delta_min": round(delta_min, 1),
                    "threshold_min": threshold,
                })

                # Only alert once per agent per stale period
                if agent_id not in self._alerted:
                    _post_p1_alert(agent_id, name, delta_min)
                    _write_audit_line(f"P1: {name} ({agent_id}) stale for {int(delta_min)}m (threshold: {threshold}m)")
                    self._alerted.add(agent_id)
                    alert_count["p1"] += 1
            else:
                # Agent is fresh — clear alert state
                self._alerted.discard(agent_id)

        # ── Write own context dump ──
        if stale:
            self._write_monitor_dump(stale, alert_count)

        return stale

    def _write_monitor_dump(self, stale_list: list, alert_count: dict):
        """Write Agent 12's own context dump."""
        try:
            from context_dump_writer import dump
            dump.save(
                agent_id="12",
                agent_name="Alert Monitor",
                action_type="stale_check",
                summary=f"Found {len(stale_list)} stale agent(s)",
                data={
                    "health_status": "RED" if len(stale_list) > 3 else ("YELLOW" if stale_list else "GREEN"),
                    "active_agents": len(AGENT_SLUGS),
                    "total_agents": 31,
                    "stale_agents": [f"{s['agent_name']} ({s['agent_id']}): {s['delta_min']}m" for s in stale_list],
                    "p0": alert_count.get("p0", 0),
                    "p1": alert_count.get("p1", 0),
                    "p2": alert_count.get("p2", 0),
                    "alerts_fired": [f"P1: {s['agent_name']} stale {s['delta_min']}m > {s['threshold_min']}m" for s in stale_list],
                    "budget_spent": 0,
                    "budget_limit": 50,
                    "budget_pct": 0,
                    "burn_rate": 0,
                    "next_check": f"In {self.poll_interval} seconds",
                }
            )
        except Exception:
            pass

    def start(self):
        """Start the stale detection loop in a background thread."""
        if self._running:
            return

        self._running = True

        def _loop():
            print(f"[Stale Detector] Started: polling every {self.poll_interval}s")
            while self._running:
                try:
                    stale = self.check_once()
                    if stale:
                        names = ", ".join(f"{s['agent_name']}({s['delta_min']}m)" for s in stale)
                        print(f"[Stale Detector] ⚠️ Stale: {names}")
                except Exception as e:
                    print(f"[Stale Detector] Error: {e}")
                time.sleep(self.poll_interval)

        self._thread = threading.Thread(target=_loop, daemon=True, name="stale-detector")
        self._thread.start()

    def stop(self):
        self._running = False


# ─── CLI entry point ───
if __name__ == "__main__":
    import json
    detector = StaleDetector(poll_interval=60)
    print("[Stale Detector] Running single check...")
    results = detector.check_once()
    if results:
        print(json.dumps(results, indent=2))
    else:
        print("All agents fresh (or none active).")

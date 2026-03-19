"""
telemetry_writer.py — Structured event logger for CoconutOS.

Usage:
    from telemetry_writer import telemetry
    telemetry.emit("llm_call_complete", "data-kitchen", agent_id="05w",
                   data={"model": "claude-4.6-opus", "cost_usd": 0.03})

Writes to:
    ~/.coconutos/logs/master.jsonl          (everything)
    ~/.coconutos/logs/by-project/{id}.jsonl (per-project)
    ~/.coconutos/logs/by-agent/agent-{id}.jsonl (per-agent)
    ~/.coconutos/logs/by-type/{type}.jsonl  (per-subsystem)
"""

import json
import os
import uuid
import time
from pathlib import Path
from datetime import datetime, timezone
from threading import Lock

LOG_DIR = Path(os.environ.get("COCONUTOS_LOG_DIR",
               os.path.expanduser("~/.coconutos/logs")))
STATE_DIR = LOG_DIR.parent / "state"


def _ensure_dirs():
    for d in [LOG_DIR, LOG_DIR / "by-project", LOG_DIR / "by-agent",
              LOG_DIR / "by-type", STATE_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    pj = STATE_DIR / "projects.json"
    if not pj.exists():
        pj.write_text("[]")


_ensure_dirs()


_TYPE_FILES = {
    "llm_call_start": "llm-calls", "llm_call_complete": "llm-calls",
    "llm_call_failed": "llm-calls", "llm_budget_denied": "llm-calls",
    "slack_message_sent": "slack-events", "slack_message_received": "slack-events",
    "trello_card_created": "trello-events", "trello_card_moved": "trello-events",
    "trello_comment_added": "trello-events",
    "git_commit": "git-events", "git_blocked": "git-events",
    "agent_spawned": "supervisor", "agent_ready": "supervisor",
    "agent_killed": "supervisor", "agent_restart": "supervisor",
    "agent_status_change": "supervisor", "agent_heartbeat": "supervisor",
    "alert_fired": "alerts", "alert_resolved": "alerts",
}


def _categorize(event_type: str) -> str:
    if event_type.startswith("llm_"): return "inference"
    if event_type.startswith("agent_"): return "lifecycle"
    if event_type.startswith("task_"): return "tasks"
    if event_type.startswith("sprint_"): return "sprints"
    if event_type.startswith("plan_") or event_type.startswith("lead_"): return "planning"
    if event_type.startswith("slack_") or event_type.startswith("trello_"): return "integrations"
    if event_type.startswith("git_"): return "git"
    if event_type.startswith("alert_"): return "alerts"
    return "system"


class TelemetryWriter:
    def __init__(self):
        self._lock = Lock()
        self._master = open(LOG_DIR / "master.jsonl", "a", buffering=1)

    def emit(self, event_type: str, project_id: str = None,
             agent_id: str = None, trace_id: str = None,
             session_id: str = None, data: dict = None,
             budget: dict = None):
        ts = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        evt_id = f"evt_{uuid.uuid4().hex[:12]}"

        event = {
            "id": evt_id,
            "ts": ts,
            "trace_id": trace_id,
            "project_id": project_id,
            "agent_id": agent_id,
            "session_id": session_id,
            "type": event_type,
            "category": _categorize(event_type),
            "data": data or {},
            "budget": budget or {},
        }

        line = json.dumps(event, separators=(",", ":")) + "\n"

        with self._lock:
            self._master.write(line)

            if project_id:
                with open(LOG_DIR / "by-project" / f"{project_id}.jsonl", "a") as f:
                    f.write(line)

            if agent_id:
                with open(LOG_DIR / "by-agent" / f"agent-{agent_id}.jsonl", "a") as f:
                    f.write(line)

            type_file = _TYPE_FILES.get(event_type)
            if type_file:
                with open(LOG_DIR / "by-type" / f"{type_file}.jsonl", "a") as f:
                    f.write(line)

        return evt_id

    def close(self):
        self._master.close()


# Singleton
telemetry = TelemetryWriter()

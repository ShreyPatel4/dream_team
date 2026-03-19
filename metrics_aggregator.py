"""
metrics_aggregator.py — Reads telemetry JSONL logs and computes dashboard metrics.

Usage:
    from metrics_aggregator import aggregator
    metrics = aggregator.compute("data-kitchen")
"""

import json
import os
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone

LOG_DIR = Path(os.environ.get("COCONUTOS_LOG_DIR",
               os.path.expanduser("~/.coconutos/logs")))
STATE_DIR = LOG_DIR.parent / "state"


class MetricsAggregator:

    def get_projects(self) -> list:
        pj = STATE_DIR / "projects.json"
        if not pj.exists():
            return []
        try:
            return json.loads(pj.read_text())
        except (json.JSONDecodeError, OSError):
            return []

    def register_project(self, project: dict) -> dict:
        projects = self.get_projects()
        record = {
            "id": project["name"].lower().replace(" ", "-").replace("_", "-"),
            "name": project["name"],
            "path": project.get("path", ""),
            "budget_usd": float(project.get("budget_usd", 50.0)),
            "departments": project.get("departments", []),
            "description": project.get("description", ""),
            "color": project.get("color", "#2d7ff9"),
            "status": "PLANNING",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        if any(p["id"] == record["id"] for p in projects):
            raise ValueError(f"Project '{record['id']}' already exists")

        projects.append(record)
        (STATE_DIR / "projects.json").write_text(json.dumps(projects, indent=2))
        (LOG_DIR / "by-project" / f"{record['id']}.jsonl").touch()

        try:
            from telemetry_writer import telemetry
            telemetry.emit("project_registered", record["id"],
                           data={"name": record["name"], "budget_usd": record["budget_usd"]})
        except ImportError:
            pass

        return record

    def compute(self, project_id: str) -> dict:
        log_path = LOG_DIR / "by-project" / f"{project_id}.jsonl"
        events = self._read_events(log_path)

        projects = self.get_projects()
        project_cfg = next((p for p in projects if p["id"] == project_id), {})
        budget_total = project_cfg.get("budget_usd", 50.0)

        return {
            "project": self._project_header(project_cfg, events),
            "kpi": self._compute_kpi(events, budget_total),
            "agents": self._compute_agents(events),
            "tasks": self._compute_tasks(events),
            "budget": self._compute_budget(events, budget_total),
            "events": self._recent_events(events, limit=30),
            "sprint": self._compute_sprint(events),
            "cost_timeline": self._cost_timeline(events),
        }

    def compute_global(self) -> dict:
        """Compute metrics across ALL projects (for the default overview)."""
        master_path = LOG_DIR / "master.jsonl"
        events = self._read_events(master_path)
        projects = self.get_projects()
        total_budget = sum(p.get("budget_usd", 50.0) for p in projects) or 50.0

        return {
            "project": {
                "name": "CoconutOS Runtime",
                "status": self._derive_status(events),
                "sprint_number": 0,
                "tasks_done": sum(1 for e in events if e["type"] in ("task_completed", "task_qa_passed")),
                "tasks_total": sum(1 for e in events if e["type"] == "task_created"),
                "elapsed_seconds": self._elapsed(events),
            },
            "kpi": self._compute_kpi(events, total_budget),
            "agents": self._compute_agents(events),
            "tasks": self._compute_tasks(events),
            "budget": self._compute_budget(events, total_budget),
            "events": self._recent_events(events, limit=30),
            "sprint": {"active": False, "number": 0, "task_count": 0, "tasks_done": 0},
            "cost_timeline": self._cost_timeline(events),
            "projects": [{"id": p["id"], "name": p["name"], "color": p.get("color", "#2d7ff9"),
                          "status": p.get("status", "IDLE")} for p in projects],
        }

    # ── Internal computations ──────────────────────────────────

    def _project_header(self, cfg: dict, events: list) -> dict:
        status = self._derive_status(events) if events else cfg.get("status", "IDLE")
        return {
            "name": cfg.get("name", "Unknown"),
            "status": status,
            "sprint_number": self._compute_sprint(events).get("number", 0),
            "tasks_done": sum(1 for e in events if e["type"] in ("task_completed", "task_qa_passed")),
            "tasks_total": sum(1 for e in events if e["type"] == "task_created"),
            "elapsed_seconds": self._elapsed(events),
        }

    def _derive_status(self, events: list) -> str:
        for e in reversed(events):
            if e["type"] == "sprint_started": return "EXECUTING"
            if e["type"] == "sprint_completed": return "IDLE"
            if e["type"] == "agent_status_change" and e.get("data", {}).get("to_status") == "EXECUTING":
                return "EXECUTING"
        return "IDLE"

    def _elapsed(self, events: list) -> int:
        if not events:
            return 0
        try:
            first_ts = datetime.fromisoformat(events[0]["ts"].replace("Z", "+00:00"))
            return int((datetime.now(timezone.utc) - first_ts).total_seconds())
        except:
            return 0

    def _compute_kpi(self, events: list, budget_total: float) -> dict:
        llm = [e for e in events if e["type"] == "llm_call_complete"]
        total_cost = sum(e["data"].get("cost_usd", 0) for e in llm)
        total_tokens = sum(e["data"].get("input_tokens", 0) +
                          e["data"].get("output_tokens", 0) for e in llm)
        total_calls = len(llm)

        spawned = set()
        killed = set()
        for e in events:
            if e["type"] == "agent_spawned": spawned.add(e.get("agent_id"))
            elif e["type"] == "agent_killed": killed.add(e.get("agent_id"))
        active = spawned - killed

        burn_rate = 0.0
        if len(llm) >= 2:
            try:
                t0 = datetime.fromisoformat(llm[0]["ts"].replace("Z", "+00:00"))
                t1 = datetime.fromisoformat(llm[-1]["ts"].replace("Z", "+00:00"))
                mins = max((t1 - t0).total_seconds() / 60, 0.1)
                burn_rate = total_cost / mins
            except:
                pass

        pct = round((total_cost / budget_total * 100), 1) if budget_total else 0

        return {
            "active_agents": len(active),
            "total_agents": 31,
            "total_cost": round(total_cost, 4),
            "budget_limit": budget_total,
            "budget_pct": min(pct, 100.0),
            "burn_rate": round(burn_rate, 4),
            "est_hourly": round(burn_rate * 60, 2),
            "llm_calls": total_calls,
            "total_tokens": total_tokens,
        }

    def _compute_agents(self, events: list) -> list:
        agents = {}
        for e in events:
            aid = e.get("agent_id")
            if not aid:
                continue
            if aid not in agents:
                agents[aid] = {"id": aid, "name": aid, "status": "IDLE",
                               "cost": 0.0, "tokens": 0, "llm_calls": 0,
                               "current_task": None, "pct": 0}

            if e["type"] == "agent_spawned":
                agents[aid]["name"] = e["data"].get("role", aid)
                agents[aid]["status"] = "INITIALIZING"
            elif e["type"] == "agent_status_change":
                agents[aid]["status"] = e["data"].get("to_status", "IDLE")
            elif e["type"] == "agent_killed":
                agents[aid]["status"] = "STANDBY"
            elif e["type"] == "llm_call_complete":
                agents[aid]["cost"] += e["data"].get("cost_usd", 0)
                agents[aid]["tokens"] += (e["data"].get("input_tokens", 0) +
                                         e["data"].get("output_tokens", 0))
                agents[aid]["llm_calls"] += 1

        result = list(agents.values())
        max_cost = max((a["cost"] for a in result), default=1) or 1
        for a in result:
            a["cost"] = round(a["cost"], 4)
            a["pct"] = int((a["cost"] / max_cost) * 100) if max_cost else 0
        return sorted(result, key=lambda x: x["cost"], reverse=True)

    def _compute_tasks(self, events: list) -> list:
        tasks = {}
        for e in events:
            d = e.get("data", {})
            if e["type"] == "task_created":
                tid = d.get("task_id", d.get("title", ""))
                tasks[tid] = {
                    "id": tid, "title": d.get("title", tid),
                    "status": "TODO", "assigned_to": d.get("assigned_to"),
                    "priority": d.get("priority", "P2"), "cost": 0.0,
                }
            elif e["type"] == "task_status_change":
                tid = d.get("task_id", "")
                if tid in tasks:
                    tasks[tid]["status"] = d.get("to_status", tasks[tid]["status"])
            elif e["type"] == "task_completed":
                tid = d.get("task_id", "")
                if tid in tasks:
                    tasks[tid]["status"] = "DONE"
                    tasks[tid]["cost"] = round(d.get("total_cost_usd", 0), 4)
            elif e["type"] == "task_qa_passed":
                tid = d.get("task_id", "")
                if tid in tasks: tasks[tid]["status"] = "DONE"
            elif e["type"] == "task_qa_failed":
                tid = d.get("task_id", "")
                if tid in tasks: tasks[tid]["status"] = "IN_PROGRESS"

        order = {"DONE": 0, "IN_PROGRESS": 1, "IN_REVIEW": 2, "QA_GATE": 3, "TODO": 4, "BACKLOG": 5}
        return sorted(tasks.values(), key=lambda t: order.get(t["status"], 9))

    def _compute_budget(self, events: list, budget_total: float) -> dict:
        by_agent = defaultdict(float)
        by_model = defaultdict(float)
        by_provider = defaultdict(float)

        for e in events:
            if e["type"] == "llm_call_complete":
                cost = e["data"].get("cost_usd", 0)
                by_agent[e.get("agent_id", "?")] += cost
                by_model[e["data"].get("model", "?")] += cost
                by_provider[e["data"].get("provider", "?")] += cost

        return {
            "total": budget_total,
            "spent": round(sum(by_agent.values()), 4),
            "by_agent": {k: round(v, 4) for k, v in sorted(by_agent.items(), key=lambda x: -x[1])},
            "by_model": {k: round(v, 4) for k, v in sorted(by_model.items(), key=lambda x: -x[1])},
            "by_provider": {k: round(v, 4) for k, v in sorted(by_provider.items(), key=lambda x: -x[1])},
        }

    def _compute_sprint(self, events: list) -> dict:
        for e in reversed(events):
            if e["type"] == "sprint_started":
                sd = e["data"]
                done = sum(1 for ev in events
                           if ev["type"] in ("task_completed", "task_qa_passed")
                           and ev["ts"] >= e["ts"])
                return {
                    "active": True, "number": sd.get("sprint_number", 1),
                    "task_count": sd.get("task_count", 0), "tasks_done": done,
                }
        return {"active": False, "number": 0, "task_count": 0, "tasks_done": 0}

    def _recent_events(self, events: list, limit: int = 30) -> list:
        READABLE = {
            "llm_call_complete", "agent_spawned", "agent_killed",
            "agent_status_change", "task_created", "task_completed",
            "task_status_change", "task_qa_passed", "task_qa_failed",
            "plan_inference", "lead_assessment", "plan_finalized",
            "sprint_started", "sprint_completed", "slack_message_sent",
            "slack_message_received", "trello_card_created",
            "git_commit", "escalation", "alert_fired", "project_registered",
        }
        filtered = [e for e in events if e["type"] in READABLE]
        recent = filtered[-limit:]

        result = []
        for e in recent:
            try:
                t = datetime.fromisoformat(e["ts"].replace("Z", "+00:00"))
                time_str = t.strftime("%H:%M")
            except:
                time_str = "??:??"
            result.append({
                "time": time_str, "agent": e.get("agent_id", "sys"),
                "type": e["type"], "message": self._msg(e),
            })
        return result

    def _msg(self, e: dict) -> str:
        t, d = e["type"], e.get("data", {})
        if t == "llm_call_complete":
            tok = d.get("input_tokens", 0) + d.get("output_tokens", 0)
            return f"LLM → {d.get('model','?')} ({tok} tok, ${d.get('cost_usd',0):.3f})"
        if t == "agent_spawned":
            return f"Spawned: {d.get('role','?')}"
        if t == "agent_killed":
            return f"Killed ({d.get('reason','done')})"
        if t == "agent_status_change":
            return f"{d.get('from_status','?')} → {d.get('to_status','?')}"
        if t == "task_created":
            return f"Task: {d.get('title','?')}"
        if t == "task_completed":
            return f"Done: {d.get('task_id','?')}"
        if t == "task_qa_passed":
            return f"QA ✓ {d.get('task_id','?')}"
        if t == "task_qa_failed":
            return f"QA ✗ {d.get('task_id','?')}"
        if t == "sprint_started":
            return f"Sprint {d.get('sprint_number',1)} started"
        if t == "slack_message_sent":
            return f"Slack → {d.get('channel_name','?')}"
        if t == "slack_message_received":
            return f"Slack ← mention received"
        if t == "trello_card_created":
            return f"Trello card: {d.get('title','?')}"
        if t == "alert_fired":
            return f"Alert: {d.get('rule_name','?')}"
        if t == "project_registered":
            return f"Project: {d.get('name','?')}"
        return t

    def _cost_timeline(self, events: list) -> list:
        llm = [e for e in events if e["type"] == "llm_call_complete"]
        running, out = 0.0, []
        for e in llm:
            running += e["data"].get("cost_usd", 0)
            out.append({"ts": e["ts"], "cost": round(running, 4),
                         "agent": e.get("agent_id"), "model": e["data"].get("model")})
        return out

    def _read_events(self, path: Path) -> list:
        if not path.exists():
            return []
        events = []
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        return events


# Singleton
aggregator = MetricsAggregator()

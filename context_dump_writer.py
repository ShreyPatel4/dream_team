"""
context_dump_writer.py — Agent 00 Post-Action Hook

Fires after EVERY agent action. Writes:
  1. One-liner to audit-log/YYYY-MM-DD.md
  2. Full context dump to context-dumps/<agent-name>/YYYY-MM-DD/<filename>

Usage:
    from context_dump_writer import dump
    dump.save(agent_id="08", agent_name="Chief Orchestrator",
              action_type="llm_call_complete", summary="Planned data-kitchen sprint 1",
              project="data-kitchen", data={...})
"""

import os
import json
from pathlib import Path
from datetime import datetime
from threading import Lock

PROJECT_ROOT = Path(os.path.dirname(os.path.abspath(__file__)))
DUMP_DIR = PROJECT_ROOT / "context-dumps"
AUDIT_DIR = PROJECT_ROOT / "audit-log"

# ─── Agent metadata for schema selection ───
AGENT_META = {
    "08": {"name": "chief_orchestrator", "slug": "chief-08", "schema": "chief"},
    "01": {"name": "product_owner", "slug": "po-01", "schema": "lead"},
    "02": {"name": "project_manager", "slug": "pm-02", "schema": "pm"},
    "03": {"name": "tech_lead", "slug": "tl-03", "schema": "lead"},
    "04": {"name": "lead_data_eng", "slug": "de-04", "schema": "lead"},
    "05": {"name": "lead_swe", "slug": "swe-05", "schema": "lead"},
    "06": {"name": "lead_ops", "slug": "ops-06", "schema": "lead"},
    "07d": {"name": "ciso", "slug": "sec-07d", "schema": "lead"},
    "09": {"name": "research_scientist", "slug": "res-09", "schema": "lead"},
    "10": {"name": "qa_lead", "slug": "qa-10", "schema": "lead"},
    "11": {"name": "git_guardian", "slug": "git-11", "schema": "monitor"},
    "12": {"name": "alert_monitor", "slug": "mon-12", "schema": "monitor"},
    "00": {"name": "org_governance", "slug": "gov-00", "schema": "monitor"},
    "01w": {"name": "product_analyst", "slug": "pa-01w", "schema": "worker"},
    "02w": {"name": "scrum_master", "slug": "sm-02w", "schema": "worker"},
    "03w": {"name": "solutions_architect", "slug": "sa-03w", "schema": "worker"},
    "04w": {"name": "sr_data_engineer", "slug": "de-04w", "schema": "worker"},
    "04w2": {"name": "data_quality_eng", "slug": "dq-04w2", "schema": "worker"},
    "05w": {"name": "sr_swe_backend", "slug": "swe-05w", "schema": "worker"},
    "05w2": {"name": "swe_systems", "slug": "sys-05w2", "schema": "worker"},
    "05w3": {"name": "swe_frontend", "slug": "fe-05w3", "schema": "worker"},
    "06w": {"name": "devops_engineer", "slug": "devops-06w", "schema": "worker"},
    "06w2": {"name": "mlops_engineer", "slug": "mlops-06w2", "schema": "worker"},
    "06w3": {"name": "gpu_infra_eng", "slug": "gpu-06w3", "schema": "worker"},
    "07a": {"name": "redteam_analysts", "slug": "rt-07a", "schema": "worker"},
    "07b": {"name": "compliance_eng", "slug": "comp-07b", "schema": "worker"},
    "07c": {"name": "security_tester", "slug": "st-07c", "schema": "worker"},
    "07w": {"name": "security_automation", "slug": "secauto-07w", "schema": "worker"},
    "09w": {"name": "research_engineer", "slug": "re-09w", "schema": "worker"},
    "10w": {"name": "qa_engineer", "slug": "qa-10w", "schema": "worker"},
    "10w2": {"name": "qa_automation", "slug": "qauto-10w2", "schema": "worker"},
}


class ContextDumpWriter:
    def __init__(self):
        self._lock = Lock()

    def save(self, agent_id: str, agent_name: str = None,
             action_type: str = "unknown", summary: str = "",
             project: str = "default", data: dict = None,
             trace_id: str = None, ticket: str = None):
        """
        Write audit log line + full context dump after every agent action.
        """
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        ts_str = now.strftime("%Y%m%d_%H%M%S")
        data = data or {}

        meta = AGENT_META.get(agent_id, {
            "name": agent_name or f"agent_{agent_id}",
            "slug": f"agent-{agent_id}",
            "schema": "worker"
        })
        name_slug = meta["name"]
        dir_slug = meta["slug"]
        schema = meta["schema"]

        # ── 1. Audit log one-liner ──
        self._write_audit_line(date_str, time_str, agent_name or name_slug,
                               action_type, summary)

        # ── 2. Full context dump ──
        filename = f"{name_slug}_{agent_id}_{project}_{ts_str}_context_progress_audit_log.md"
        dump_dir = DUMP_DIR / dir_slug / date_str
        dump_dir.mkdir(parents=True, exist_ok=True)
        dump_path = dump_dir / filename

        content = self._render_dump(schema, agent_id, agent_name or name_slug,
                                     now, project, action_type, summary,
                                     data, trace_id, ticket)

        with self._lock:
            dump_path.write_text(content)

        return str(dump_path)

    def _write_audit_line(self, date_str: str, time_str: str,
                          agent_name: str, action_type: str, summary: str):
        AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        log_file = AUDIT_DIR / f"{date_str}.md"

        line = f"[{time_str}] {agent_name} | {action_type} | {summary}\n"

        with self._lock:
            with open(log_file, "a") as f:
                if log_file.stat().st_size == 0:
                    f.write(f"# Audit Log — {date_str}\n\n")
                f.write(line)

    def _render_dump(self, schema: str, agent_id: str, agent_name: str,
                     now: datetime, project: str, action_type: str,
                     summary: str, data: dict, trace_id: str, ticket: str) -> str:

        ts = now.strftime("%Y-%m-%d %H:%M:%S")

        if schema == "chief":
            return self._chief_dump(agent_id, agent_name, ts, project,
                                     action_type, summary, data, trace_id)
        elif schema == "pm":
            return self._pm_dump(agent_id, agent_name, ts, project,
                                  action_type, summary, data)
        elif schema == "monitor":
            return self._monitor_dump(agent_id, agent_name, ts,
                                       action_type, summary, data)
        else:
            return self._worker_dump(agent_id, agent_name, ts, project,
                                      action_type, summary, data, ticket)

    def _chief_dump(self, aid, name, ts, project, action, summary, data, trace_id):
        return f"""# Context Dump: Chief Orchestrator ({aid})
## Timestamp: {ts}
## Project: {project}
## Session ID: {trace_id or 'N/A'}

### Current State
- Status: {data.get('status', 'UNKNOWN')}
- Active project: {project}
- Sprint: {data.get('sprint_number', 'N/A')} (tasks done: {data.get('tasks_done', 0)}/{data.get('tasks_total', 0)})

### Action Performed
- Type: {action}
- Summary: {summary}
- LLM model used: {data.get('model', 'N/A')}
- Cost: ${data.get('cost_usd', 0):.4f}
- Duration: {data.get('latency_ms', 0)}ms

### Plan State
- Tasks delegated: {data.get('tasks_delegated', 0)}
- Agents active: {', '.join(data.get('agents_active', [])) or 'none'}
- Agents pending: {', '.join(data.get('agents_pending', [])) or 'none'}
- Blockers: {', '.join(data.get('blockers', [])) or 'none'}

### Context Files Read
{self._fmt_list(data.get('files_read', []))}

### Decisions Made
{self._fmt_list(data.get('decisions', []))}

### Next Action
- {data.get('next_action', 'Awaiting trigger')}
"""

    def _worker_dump(self, aid, name, ts, project, action, summary, data, ticket):
        return f"""# Context Dump: {name} ({aid})
## Timestamp: {ts}
## Project: {project}
## Ticket: {ticket or data.get('ticket', 'N/A')}

### Current State
- Status: {data.get('status', 'IDLE')}
- Ticket: {ticket or data.get('ticket', 'N/A')}
- Task: {data.get('task_title', 'N/A')}

### Action Performed
- Type: {action}
- Summary: {summary}
- Files touched: {', '.join(data.get('files_touched', [])) or 'none'}

### Progress
- Acceptance criteria met: {data.get('criteria_met', 0)}/{data.get('criteria_total', 0)}
- Tests passing: {data.get('tests_passing', 0)}/{data.get('tests_total', 0)}
- Estimated completion: {data.get('completion_pct', 0)}%

### Code Changes
- Files modified: {', '.join(data.get('files_modified', [])) or 'none'}
- Lines added/removed: +{data.get('lines_added', 0)} / -{data.get('lines_removed', 0)}

### Blockers
- {', '.join(data.get('blockers', [])) or 'none'}

### Next Action
- {data.get('next_action', 'Awaiting assignment')}
"""

    def _pm_dump(self, aid, name, ts, project, action, summary, data):
        agent_table = ""
        for a in data.get("agent_statuses", []):
            agent_table += f"| {a.get('id','?')} | {a.get('status','?')} | {a.get('last_dump','?')} | {a.get('stale','NO')} |\n"
        if not agent_table:
            agent_table = "| — | — | — | — |\n"

        return f"""# Context Dump: Project Manager ({aid})
## Timestamp: {ts}
## Project: {project}
## Sprint: {data.get('sprint_number', 'N/A')}

### Current State
- Status: {data.get('status', 'COORDINATING')}
- Sprint: {data.get('sprint_number', 'N/A')} (day {data.get('sprint_day', '?')} of {data.get('sprint_length', '?')})

### Action Performed
- Type: {action}
- Summary: {summary}

### Sprint Health
- Tasks total: {data.get('tasks_total', 0)}
- In progress: {data.get('in_progress', 0)} (agents: {', '.join(data.get('ip_agents', [])) or 'none'})
- Blocked: {data.get('blocked', 0)} (blockers: {', '.join(data.get('blocker_details', [])) or 'none'})
- In QA: {data.get('in_qa', 0)}
- Done: {data.get('done', 0)}

### Agent Status
| Agent | Status | Last Dump | Stale? |
|-------|--------|-----------|--------|
{agent_table}
### Kanban Sync
- Trello ↔ local drift: {data.get('kanban_drift', 0)} discrepancies
- Action taken: {data.get('kanban_action', 'none')}

### Next Action
- {data.get('next_action', 'Awaiting next sweep')}
"""

    def _monitor_dump(self, aid, name, ts, action, summary, data):
        alerts = ""
        for a in data.get("alerts_fired", []):
            alerts += f"- {a}\n"
        if not alerts:
            alerts = "- none\n"

        return f"""# Context Dump: {name} ({aid})
## Timestamp: {ts}

### Action Performed
- Type: {action}
- Summary: {summary}

### Org Health
- Status: {data.get('health_status', 'GREEN')}
- Active agents: {data.get('active_agents', 0)}/{data.get('total_agents', 31)}
- Stale agents: {', '.join(data.get('stale_agents', [])) or 'none'}
- Open alerts: P0:{data.get('p0', 0)} P1:{data.get('p1', 0)} P2:{data.get('p2', 0)}

### Alerts Fired This Session
{alerts}
### Budget
- Spent: ${data.get('budget_spent', 0):.2f} / ${data.get('budget_limit', 50):.2f} ({data.get('budget_pct', 0):.1f}%)
- Burn rate: ${data.get('burn_rate', 0):.4f}/min

### Next Check
- {data.get('next_check', 'In 60 seconds')}
"""

    def _fmt_list(self, items):
        if not items:
            return "- none"
        return "\n".join(f"- {item}" for item in items)


# Singleton
dump = ContextDumpWriter()

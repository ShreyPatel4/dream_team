"""
CoconutOS Dream Team — Dashboard Server v3 (Telemetry-Powered)
Serves the real-time agent monitoring dashboard and REST APIs.
Data is computed from JSONL telemetry logs via metrics_aggregator.
Falls back to Prometheus + filesystem for backward compatibility.
"""
import os
import json
import time
import glob
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import urllib.request
import urllib.parse

from metrics_aggregator import aggregator

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PROMETHEUS_URL = "http://localhost:9090"
HOME_DIR = os.path.expanduser("~")
CONTEXT_STORE = os.path.join(HOME_DIR, ".gemini", "antigravity", "context-store")
NOTEBOOKS_DIR = os.path.join(HOME_DIR, ".gemini", "antigravity", "notebooks")

BOOT_TIME = time.time()

# ─── Agent Registry (for fallback mode) ───
AGENT_REGISTRY = {
    "08": {"name": "Chief Orchestrator", "role": "lead"},
    "01": {"name": "Product Owner", "role": "lead"},
    "02": {"name": "Project Manager", "role": "lead"},
    "03": {"name": "Tech Lead", "role": "lead"},
    "04": {"name": "Lead Data Eng", "role": "lead"},
    "05": {"name": "Lead SWE", "role": "lead"},
    "06": {"name": "Lead Ops", "role": "lead"},
    "07d": {"name": "CISO", "role": "lead"},
    "09": {"name": "Research Scientist", "role": "lead"},
    "10": {"name": "QA Lead", "role": "lead"},
    "11": {"name": "Git Guardian", "role": "sentinel"},
    "12": {"name": "Alert Monitor", "role": "sentinel"},
    "00": {"name": "Org Governance", "role": "lead"},
    "01w": {"name": "Product Analyst", "role": "worker"},
    "02w": {"name": "Scrum Master", "role": "worker"},
    "03w": {"name": "Solutions Architect", "role": "worker"},
    "04w": {"name": "Sr Data Eng", "role": "worker"},
    "04w2": {"name": "Data Quality Eng", "role": "worker"},
    "05w": {"name": "Sr SWE Backend", "role": "worker"},
    "05w2": {"name": "SWE Systems", "role": "worker"},
    "05w3": {"name": "SWE Frontend", "role": "worker"},
    "06w": {"name": "DevOps Engineer", "role": "worker"},
    "06w2": {"name": "MLOps Engineer", "role": "worker"},
    "06w3": {"name": "GPU/CUDA Eng", "role": "worker"},
    "07a": {"name": "Security Analyst", "role": "worker"},
    "07b": {"name": "Compliance Eng", "role": "worker"},
    "07c": {"name": "Security Tester", "role": "worker"},
    "07w": {"name": "Security Automation", "role": "worker"},
    "09w": {"name": "Research Engineer", "role": "worker"},
    "10w": {"name": "QA Engineer", "role": "worker"},
    "10w2": {"name": "QA Automation", "role": "worker"},
}


def query_prometheus(query):
    try:
        url = f"{PROMETHEUS_URL}/api/v1/query?query={urllib.parse.quote(query)}"
        with urllib.request.urlopen(url, timeout=2) as resp:
            data = json.loads(resp.read().decode())
            if data.get("status") == "success":
                return data.get("data", {}).get("result", [])
    except Exception:
        pass
    return []


def scan_notebooks():
    events = []
    if not os.path.isdir(NOTEBOOKS_DIR):
        return events
    for folder in sorted(os.listdir(NOTEBOOKS_DIR)):
        agent_path = os.path.join(NOTEBOOKS_DIR, folder)
        if not os.path.isdir(agent_path):
            continue
        agent_id = folder.replace("agent-", "")
        for fname in sorted(os.listdir(agent_path)):
            fpath = os.path.join(agent_path, fname)
            if not os.path.isfile(fpath):
                continue
            mtime = os.path.getmtime(fpath)
            events.append({
                "time": datetime.fromtimestamp(mtime).strftime("%H:%M"),
                "agent": agent_id,
                "message": f"Updated {fname}",
                "ts": mtime
            })
    events.sort(key=lambda x: x["ts"], reverse=True)
    return [{"time": e["time"], "agent": e["agent"], "message": e["message"]} for e in events[:25]]


def build_fallback_state():
    """Legacy: compute from Prometheus + filesystem when no telemetry exists."""
    llm_results = query_prometheus("dreamteam_llm_calls_total")
    budget_results = query_prometheus("dreamteam_budget_spent_usd")
    tasks_results = query_prometheus("dreamteam_tasks_completed_total")

    agent_call_counts = {}
    total_calls = 0
    for entry in llm_results:
        aid = entry.get("metric", {}).get("agent_id", "?")
        val = int(float(entry.get("value", [0, 0])[1]))
        agent_call_counts[aid] = agent_call_counts.get(aid, 0) + val
        total_calls += val

    total_cost = 0.0
    for entry in budget_results:
        total_cost = float(entry.get("value", [0, 0])[1])

    total_tasks_done = 0
    for entry in tasks_results:
        total_tasks_done += int(float(entry.get("value", [0, 0])[1]))

    elapsed_sec = time.time() - BOOT_TIME
    mins, secs = divmod(int(elapsed_sec), 60)
    hrs, mins_r = divmod(mins, 60)
    elapsed_str = f"{hrs}h {mins_r}m {secs}s" if hrs else f"{mins_r}m {secs}s"
    elapsed_min = max(elapsed_sec / 60.0, 1.0)
    burn_rate = total_cost / elapsed_min

    inbox_dir = os.path.join(CONTEXT_STORE, "inbox")
    inbox_count = len(glob.glob(os.path.join(inbox_dir, "*.md"))) if os.path.isdir(inbox_dir) else 0
    status = "EXECUTING" if inbox_count > 0 else ("MONITORING" if total_calls > 0 else "IDLE")

    agents = []
    active_count = 0
    max_calls = max(agent_call_counts.values()) if agent_call_counts else 1
    for aid, info in AGENT_REGISTRY.items():
        calls = agent_call_counts.get(aid, 0)
        cost = round(calls * 0.01, 2)
        tokens = calls * 4500
        pct = int((calls / max_calls) * 100) if max_calls > 0 and calls > 0 else 0

        if calls > 0:
            agent_status = "EXECUTING"
            active_count += 1
        elif info["role"] == "sentinel":
            agent_status = "WATCHING"
            active_count += 1
        elif aid == "08":
            agent_status = "IDLE"
            active_count += 1
        else:
            agent_status = "STANDBY"

        agents.append({
            "id": aid, "name": info["name"], "role": info["role"],
            "status": agent_status, "cost": cost, "tokens": tokens,
            "calls": calls, "pct": pct
        })

    status_order = {"EXECUTING": 0, "REVIEWING": 1, "MONITORING": 2, "IDLE": 3, "WATCHING": 4, "STANDBY": 5}
    agents.sort(key=lambda a: (status_order.get(a["status"], 9), a["id"]))

    events = scan_notebooks()
    budget_limit = 50.0
    budget_pct = round((total_cost / budget_limit) * 100, 1) if budget_limit else 0

    return {
        "project": {"name": "Dream Team v4.3", "status": status,
                     "elapsed": elapsed_str, "tasks_done": total_tasks_done},
        "kpi": {
            "active_agents": active_count, "total_agents": len(AGENT_REGISTRY),
            "total_cost": round(total_cost, 2), "budget_limit": budget_limit,
            "budget_pct": budget_pct, "burn_rate": round(burn_rate, 4),
            "est_hourly": round(burn_rate * 60, 2),
            "total_tokens": sum(a["tokens"] for a in agents),
            "llm_calls": total_calls,
        },
        "agents": agents,
        "events": events,
        "tasks": [],
        "budget": {"total": budget_limit, "spent": round(total_cost, 2),
                   "by_agent": {}, "by_model": {}, "by_provider": {}},
        "sprint": {"active": False, "number": 0, "task_count": 0, "tasks_done": 0},
        "cost_timeline": [],
        "projects": [],
        "ts": datetime.now().isoformat(),
    }


def build_state(project_id=None):
    """
    Build dashboard state. Strategy:
    1. If project_id given and has JSONL data → use aggregator
    2. If global and JSONL master has data → use aggregator.compute_global()
    3. Fallback → Prometheus + filesystem scan (backward compat)
    """
    try:
        if project_id:
            metrics = aggregator.compute(project_id)
            if metrics["events"] or metrics["kpi"]["llm_calls"] > 0:
                return metrics
        else:
            metrics = aggregator.compute_global()
            if metrics["events"] or metrics["kpi"]["llm_calls"] > 0:
                # Merge notebook events for richer timeline when telemetry is sparse
                nb_events = scan_notebooks()
                if nb_events and not metrics["events"]:
                    metrics["events"] = nb_events
                return metrics
    except Exception as e:
        print(f"[Dashboard] Aggregator error: {e}")

    # Fallback to legacy Prometheus + filesystem
    state = build_fallback_state()
    # Merge in registered projects for tab rendering
    try:
        state["projects"] = [{"id": p["id"], "name": p["name"],
                              "color": p.get("color", "#2d7ff9"),
                              "status": p.get("status", "IDLE")}
                             for p in aggregator.get_projects()]
    except:
        pass
    return state


class DashboardHandler(SimpleHTTPRequestHandler):

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path in ("", "/dashboard"):
            self._serve_file("dashboard.html", "text/html")

        elif path == "/api/state":
            # Check for project filter
            params = parse_qs(parsed.query)
            project_id = params.get("project", [None])[0]
            state = build_state(project_id)
            self._json_response(state)

        elif path == "/api/projects":
            projects = aggregator.get_projects()
            self._json_response(projects)

        elif path.startswith("/api/project/"):
            pid = path.split("/")[-1]
            metrics = aggregator.compute(pid)
            self._json_response(metrics)

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "/api/projects":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            try:
                project = aggregator.register_project(body)
                self._json_response(project, 201)
            except ValueError as e:
                self._json_response({"error": str(e)}, 409)
            except Exception as e:
                self._json_response({"error": str(e)}, 500)
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Project-Id")
        self.end_headers()

    def _serve_file(self, filename, content_type):
        fpath = os.path.join(PROJECT_ROOT, filename)
        if not os.path.exists(fpath):
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Cache-Control", "public, max-age=3600")
        self.end_headers()
        with open(fpath, "rb") as f:
            self.wfile.write(f.read())

    def _json_response(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-cache, no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Project-Id")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())

    def log_message(self, fmt, *args):
        pass


def run(port=5050):
    print(f"\n🖥️  CoconutOS Dashboard v3 (Telemetry-Powered)")
    print(f"   Dashboard  → http://localhost:{port}")
    print(f"   API State  → http://localhost:{port}/api/state")
    print(f"   Projects   → http://localhost:{port}/api/projects")
    print(f"   Per-Project→ http://localhost:{port}/api/project/{{id}}\n")
    HTTPServer(("0.0.0.0", port), DashboardHandler).serve_forever()

if __name__ == "__main__":
    run()

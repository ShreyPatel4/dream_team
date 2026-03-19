# CoconutOS Dream Team

A fully autonomous 31-agent virtual engineering organization powered by LLM inference. Agents analyze requirements, write technical specifications, debate approaches in Slack, manage a Trello board, QA each other's work, and persist context across sessions.

**Key innovation:** Inference-minimal architecture. Every routing decision, status check, sprint decomposition, and template generation is done by deterministic Python — zero LLM calls. The LLM is reserved exclusively for creative work.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Fill in your API keys in .env

# 3. Boot agents (Slack Listener + Orchestrator)
python3 coconutos_runner.py

# 4. Boot observability (requires Docker)
docker compose up -d

# 5. Boot dashboard
python3 dashboard_server.py
```

## Services

| Service | URL | Description |
|---------|-----|-------------|
| Custom Dashboard | [localhost:5050](http://localhost:5050) | Real-time agent monitoring SPA |
| Grafana | [localhost:3000](http://localhost:3000) | Auto-provisioned observability dashboards |
| Prometheus | [localhost:9090](http://localhost:9090) | Metrics scraping |
| Jaeger | [localhost:16686](http://localhost:16686) | Distributed tracing |

## Documentation

All documentation lives in the [`docs/`](docs/) folder:

| Document | Description |
|----------|-------------|
| [COCONUTOS_REFERENCE.md](docs/COCONUTOS_REFERENCE.md) | **Master reference** — single source of truth |
| [AGENT_REFERENCE.md](docs/AGENT_REFERENCE.md) | All 31 agents: behaviours, rules, skills |
| [ARCHITECTURE_V4_UNIFIED.md](docs/ARCHITECTURE_V4_UNIFIED.md) | Full v4.2 protocol specification |
| [ARCHITECTURE_EXPLAINED.md](docs/ARCHITECTURE_EXPLAINED.md) | Architecture overview |
| [CURRENT_PROGRESS.md](docs/CURRENT_PROGRESS.md) | Build phase completion tracker |
| [SETUP_GUIDE.md](docs/SETUP_GUIDE.md) | Setup instructions |
| [LIVE_DEMO_GUIDE.md](docs/LIVE_DEMO_GUIDE.md) | Live demo walkthrough |
| [setup-guides/](docs/setup-guides/) | Slack, Trello, MCP setup guides |

## Project Structure

```
dream_team/
├── coconutos_runner.py        # Process supervisor (entry point)
├── agi_orchestrator.py        # Agent 08 brain — the AGI loop
├── llm_gateway.py             # Multi-provider LLM router
├── slack_listener.py          # Slack Socket Mode daemon
├── slack_worker.py            # Slack message poster
├── trello_worker.py           # Trello API client
├── telemetry_writer.py        # JSONL event logger
├── metrics_aggregator.py      # Telemetry → dashboard metrics
├── dashboard_server.py        # REST API + dashboard server (:5050)
├── dashboard.html             # Real-time monitoring SPA
├── alert_monitor.py           # Budget + stuck agent detection
├── request_classifier.py      # Deterministic request routing (0 API)
├── consensus_checker.py       # Lead agreement check (0 API)
├── sprint_decomposer.py       # Topological task sorting (0 API)
├── approach_auto_approver.py  # Auto-approve proposals (0 API)
├── template_engine.py         # Structured output templates (0 API)
├── context_progress_writer.py # Auto-update project state (0 API)
├── sweep_notebooks.py         # Harvest all 31 notebooks
├── update_all_skills.py       # Regenerate SKILL.md files
├── coconutos.yml              # LLM model routing config
├── docker-compose.yml         # Grafana + Prometheus + Jaeger
├── prometheus.yml             # Scrape config
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variable template
├── docs/                      # All documentation
├── global-skills/             # 31 agent SKILL.md persona files
├── global-rules/              # Organization constitution
├── grafana/                   # Auto-provisioned dashboards
├── context-store/             # Project state + inbox triggers
├── project-tracker/           # Sprint & Kanban state
└── notebooks/                 # 31 agent working memory
```

## LLM Configuration

Models are configured in `coconutos.yml`:
- **Gemini 3.1 Pro** — Chief Orchestrator (Agent 08)
- **Claude 4.6 Opus** — All leads and workers (code + review)
- **Ollama** — Local fallback (Qwen 2.5, DeepSeek-Coder)

## License

Private — Coconut Labs.

# CoconutOS Dream Team — Complete System Reference

**Coconut Labs · Version 4.3 · Last Updated: 2026-03-18**

> *This is the single source of truth.* It consolidates architecture, codebase structure, operational procedures, setup instructions, and project progress into one document. If anything in `README.md`, `ARCHITECTURE_EXPLAINED.md`, `SETUP_GUIDE.md`, or `CURRENT_PROGRESS.md` conflicts with this file, **this file wins.**

---

## Table of Contents

1. [What Is This](#1-what-is-this)
2. [System Status](#2-system-status)
3. [Architecture Overview](#3-architecture-overview)
4. [Org Chart — 31 Agents](#4-org-chart--31-agents)
5. [Codebase Map](#5-codebase-map)
6. [How It Works (End-to-End)](#6-how-it-works-end-to-end)
7. [LLM Routing & Inference-Minimal Protocol](#7-llm-routing--inference-minimal-protocol)
8. [Deterministic Decision Engine](#8-deterministic-decision-engine)
9. [Template Engine](#9-template-engine)
10. [Autonomy Model](#10-autonomy-model)
11. [Governance & Security (Constitution v4)](#11-governance--security-constitution-v4)
12. [Observability Stack](#12-observability-stack)
13. [Custom Dashboard](#13-custom-dashboard)
14. [Setup Guide (OS-Agnostic)](#14-setup-guide-os-agnostic)
15. [Environment Variables](#15-environment-variables)
16. [Running the Stack](#16-running-the-stack)
17. [Build Progress & Phases](#17-build-progress--phases)
18. [Call Budget Economics](#18-call-budget-economics)
19. [Local Model Migration Path](#19-local-model-migration-path)
20. [Future Roadmap](#20-future-roadmap)

---

## 1. What Is This

The **Dream Team** is a fully autonomous 31-agent virtual engineering organization that runs on your local machine. It simulates a real software company: distinct departments (Product, Engineering, Data, DevOps, Security, QA), an org hierarchy with a chain of command, and integrations into Slack and Trello for coordination.

Agents don't just write code. They analyze requirements, write technical specifications, debate approaches in Slack, manage a Trello board, QA their peers' work, and persist their thought processes across sessions using local notebooks.

**Key innovation:** The system is **inference-minimal**. Every routing decision, status check, sprint decomposition, and template generation is done by deterministic Python code — zero LLM API calls. The LLM is reserved exclusively for creative work: strategic planning, code writing, code review, and conflict resolution.

---

## 2. System Status

| Service | Process | Port | Status |
|---------|---------|------|--------|
| `coconutos_runner.py` | Parent supervisor | — | 🟢 Running |
| `slack_listener.py` | Slack Socket Mode | — | 🟢 Listening (Coconut Labs) |
| `agi_orchestrator.py` | Chief AGI loop | 8000 (Prometheus) | 🟢 Watching inbox |
| `dashboard_server.py` | Custom dashboard | 5050 | 🟢 Serving |
| Grafana | Docker container | 3000 | 🟢 Running |
| Prometheus | Docker container | 9090 | 🟢 Scraping |
| Jaeger | Docker container | 16686 | 🟢 Tracing |

**Platform:** OS-Agnostic (macOS / Linux / Windows) — Python 3.13
**LLM Routing:** Gemini 3.1 Pro (Chief / Agent 08) · Claude 4.6 Opus (Leads + Workers)
**Workspace:** Coconut Labs Slack (`T0AL981MNP9`)

---

## 3. Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                        COCONUTOS RUNTIME                         │
│                                                                  │
│  ┌─────────────┐    ┌──────────────────┐    ┌────────────────┐  │
│  │   Slack      │───▶│  context-store/  │◀──▶│  AGI           │  │
│  │   Listener   │    │    inbox/        │    │  Orchestrator  │  │
│  │  (Socket     │    │    context_      │    │  (Agent 08     │  │
│  │   Mode)      │    │    progress.md   │    │   Brain)       │  │
│  └──────┬───────┘    └──────────────────┘    └───────┬────────┘  │
│         │                                            │           │
│         │            ┌──────────────────┐            │           │
│         └───────────▶│  LLM Gateway     │◀───────────┘           │
│                      │  ┌────────────┐  │                        │
│                      │  │ Gemini API │  │                        │
│                      │  │ Claude API │  │                        │
│                      │  │ Ollama     │  │                        │
│                      │  └────────────┘  │                        │
│                      └──────────────────┘                        │
│                                                                  │
│  ┌─────────────┐    ┌──────────────────┐    ┌────────────────┐  │
│  │ Deterministic│    │  31 Agent        │    │  Template      │  │
│  │ Modules      │    │  SKILL.md Files  │    │  Engine        │  │
│  │ • Classifier │    │  notebooks/      │    │  • Proposals   │  │
│  │ • Consensus  │    │  project-tracker/│    │  • Summaries   │  │
│  │ • Decomposer │    │                  │    │  • Trello cards│  │
│  └─────────────┘    └──────────────────┘    └────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              OBSERVABILITY LAYER                           │  │
│  │  Prometheus (metrics) → Grafana (dashboards)              │  │
│  │  OpenTelemetry → Jaeger (traces)                          │  │
│  │  AlertMonitor → Slack (#alerts)                           │  │
│  │  Dashboard Server → http://localhost:5050                 │  │
│  └───────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 4. Org Chart — 31 Agents

```
Shrey (Founder — final authority)
  └── 08. Chief Orchestrator          ← THE BRAIN. Plans, delegates, validates.
        ├── Advisory Council: 09, 03, 01, dept leads
        │
        ├── 02. Project Manager       ← Sprint planning, Trello board owner
        │     └── 02w. Scrum Master
        │
        ├── 01. Product Owner         ← Requirements, user stories
        │     └── 01w. Product Analyst
        │
        ├── 03. Tech Lead             ← Architecture decisions
        │     └── 03w. Solutions Architect
        │
        ├── 04. Lead Data Eng         ← Data pipelines, schemas
        │     ├── 04w. Sr Data Engineer
        │     └── 04w2. Data Quality Eng
        │
        ├── 05. Lead SWE              ← Software engineering
        │     ├── 05w. Sr SWE Backend
        │     ├── 05w2. SWE Systems/Rust
        │     └── 05w3. SWE Frontend
        │
        ├── 06. Lead Ops              ← Infrastructure, deployment
        │     ├── 06w. DevOps Engineer
        │     ├── 06w2. MLOps Engineer
        │     └── 06w3. GPU/CUDA/MLX Eng
        │
        ├── 07d. CISO                 ← Security leadership
        │     ├── 07a. Red Team Analysts
        │     ├── 07b. Compliance Eng
        │     ├── 07c. Security Tester
        │     └── 07w. Security Automation
        │
        ├── 09. Research Scientist    ← R&D, prior art, novel methods
        │     └── 09w. Research Engineer
        │
        ├── 10. QA Lead               ← Quality gates
        │     ├── 10w. QA Engineer
        │     └── 10w2. QA Automation
        │
        ├── 11. Git Guardian          ← Blocks git push/pull, enforces commits
        ├── 12. Alert Monitor         ← Budget burn, stuck agents, health
        └── 00. Org Governance        ← Background rule enforcement
```

---

## 5. Codebase Map

### Root Directory: `dream-team-v2/`

```
dream-team-v2/
│
├── 🧠 RUNTIME (Core Services)
│   ├── coconutos_runner.py          Cross-platform process supervisor
│   │                                 Spawns slack_listener + agi_orchestrator
│   │                                 Auto-restarts crashed services
│   │
│   ├── agi_orchestrator.py          The Chief Orchestrator (Agent 08) brain
│   │                                 Watches inbox, embeds SKILL.md rules,
│   │                                 calls LLM API, handles [HANDOFF: xx] tokens,
│   │                                 runs recursive agent execution loop
│   │
│   ├── slack_listener.py            Slack Socket Mode listener (slack_bolt)
│   │                                 Filters by workspace T0AL981MNP9
│   │                                 Writes .md payloads to inbox/
│   │
│   ├── slack_worker.py              OS-agnostic Slack message poster (Python)
│   │                                 Replaces legacy slack-bridge.sh
│   │
│   └── trello_worker.py             OS-agnostic Trello API client (Python)
│                                     Replaces legacy trello-tool.sh
│
├── 🤖 LLM LAYER
│   ├── llm_gateway.py               Multi-provider LLM router
│   │                                 Supports: gemini, claude, ollama
│   │                                 Modes: api / hybrid / local
│   │                                 Per-agent call tracking & budgets
│   │
│   └── coconutos.yml                LLM routing configuration
│                                     Model assignments by role type
│                                     Budget caps per task complexity
│
├── ⚡ DETERMINISTIC MODULES (0 API calls)
│   ├── request_classifier.py        Routes requests by keyword matching
│   ├── consensus_checker.py         Checks lead agreement (JSON parsing)
│   ├── sprint_decomposer.py         Topological sort for sprint planning
│   ├── approach_auto_approver.py    Auto-approves proposals with no concerns
│   ├── template_engine.py           Generates proposals, summaries, Trello cards
│   ├── context_progress_writer.py   Auto-updates context_progress.md
│   └── sweep_notebooks.py           Harvests progress from all 31 notebooks
│
├── 📊 OBSERVABILITY
│   ├── alert_monitor.py             Budget burn + stuck agent detection
│   ├── dashboard_server.py          REST API + static file server (:5050)
│   ├── dashboard.html               Real-time SPA (DM Sans, JetBrains Mono)
│   ├── docker-compose.yml           Grafana + Prometheus + Jaeger containers
│   └── prometheus.yml               Scrape config (targets orchestrator :8000)
│
├── 📁 DATA DIRECTORIES
│   ├── context-store/               Project state, inbox triggers
│   │   ├── inbox/                   Slack trigger payloads (.md files)
│   │   ├── context_progress.md      Single source of truth for project state
│   │   └── active_projects.json     All active project metadata
│   │
│   ├── project-tracker/             Sprint & Kanban state
│   │   ├── kanban.md                Local mirror of Trello board
│   │   └── current_sprint.md        Active sprint details
│   │
│   ├── global-rules/                Governance
│   │   └── rules.md                 Constitution v3 — immutable org rules
│   │
│   └── global-skills/               31 agent persona directories
│       ├── 00-org-governance/SKILL.md
│       ├── 01-product-owner/SKILL.md
│       ├── ...
│       └── 12-alert-monitor/SKILL.md
│
├── 📄 DOCUMENTATION
│   ├── COCONUTOS_REFERENCE.md       ← THIS FILE (master reference)
│   ├── ARCHITECTURE_V4_UNIFIED.md   Full v4.2 spec (orchestration + protocol)
│   ├── CURRENT_PROGRESS.md          Phase completion tracker
│   └── SETUP_GUIDE.md               Quick-start setup instructions
│
├── 🔒 CONFIGURATION
│   ├── .env                         API keys (gitignored)
│   ├── .gitignore                   Protects secrets
│   └── requirements.txt             Python dependencies
│
└── 📓 NOTEBOOKS (at ~/.gemini/antigravity/notebooks/)
    ├── agent-08/                    Chief's working memory
    │   ├── progress.md
    │   ├── decisions.md
    │   ├── requirements.md
    │   ├── blockers.md
    │   ├── ideas.md
    │   └── scratch/
    ├── agent-05w/                   Backend SWE's working memory
    │   └── ...
    └── ... (31 total)
```

### File-by-File Descriptions

| File | Lines | Purpose |
|------|-------|---------|
| `coconutos_runner.py` | 60 | Universal entry point. Uses `multiprocessing` to spawn `slack_listener.py` and `agi_orchestrator.py`. Catches SIGINT for clean cluster shutdown. Auto-restarts crashed children after 5s delay. |
| `agi_orchestrator.py` | ~200 | The brain. Polls `context-store/inbox/` every 10s. When a trigger arrives, loads Agent 08's SKILL.md, calls `LLMGateway` to produce a plan, parses `[HANDOFF: xx]` tokens to spawn worker agents recursively. Serves Prometheus metrics on port 8000. Integrates `AlertMonitor` for health checks. |
| `slack_listener.py` | ~90 | Slack `socket_mode` handler via `slack_bolt`. Authenticates with `xapp-` App Token, restricts to workspace `T0AL981MNP9`. Writes `.md` trigger files to inbox. Logs to `slack_listener.log`. |
| `slack_worker.py` | 48 | CLI: `python slack_worker.py <channel> <message> [--name Bot] [--emoji :robot:]`. Posts Slack messages using the `xoxb-` Bot Token. Replaces the old bash bridge. |
| `trello_worker.py` | 60 | CLI: `python trello_worker.py create|move|comment [args]`. Creates cards, moves them between lists, posts comments. Uses Trello REST API with keys from `.env`. |
| `llm_gateway.py` | ~100 | Abstraction over Gemini, Claude, and Ollama APIs. Reads `coconutos.yml` for model routing. Tracks per-agent call counts and cost. Exposes Prometheus counters. |
| `request_classifier.py` | ~60 | Deterministic request routing. Matches incoming text against active projects, detects questions, escalations, and new projects. Zero API calls. |
| `consensus_checker.py` | ~50 | Checks if all lead assessments agree. Merges refinements if present. Returns PROCEED, PROCEED_WITH_REFINEMENTS, or CHIEF_DECIDES. Zero API calls. |
| `sprint_decomposer.py` | ~70 | Topological sort. Decomposes task lists into ordered sprints respecting dependencies. Max 10 tasks per sprint. Zero API calls. |
| `approach_auto_approver.py` | ~30 | If a worker's approach proposal has no questions/concerns, auto-approves. Otherwise flags for lead review. Zero API calls. |
| `template_engine.py` | ~100 | Generates structured markdown from templates: approach proposals, sprint summaries, Trello card descriptions, requirements handoffs. Zero API calls. |
| `context_progress_writer.py` | ~80 | Writes/updates `context_progress.md` with current project state, completed tasks, in-progress work, sprint metrics. Called at session end. |
| `sweep_notebooks.py` | ~60 | Scans all 31 agent notebooks. Extracts `progress.md` and `blockers.md` for Chief/PM review. |
| `alert_monitor.py` | 66 | Tracks budget burn rate and detects stuck agents (no heartbeat in 5 min). Posts warnings to `#alerts` Slack channel. |
| `dashboard_server.py` | ~170 | HTTP server on port 5050. Serves `dashboard.html` (cached). REST API `/api/state` queries Prometheus + scans notebooks to return live JSON. |
| `dashboard.html` | ~600 | Production SPA. DM Sans + JetBrains Mono fonts. Light/dark mode. Silent JSON-only refresh every 3s. KPI cards, agent table, budget bar (shimmer animation), event timeline, ⌘K command bar. |
| `update_all_skills.py` | ~130 | Regenerates all 31 SKILL.md files. Injects Slack bot identity, Trello integration, and Python execution triggers. |
| `coconutos.yml` | 24 | LLM configuration. Modes: `api` / `hybrid` / `local`. Default models: `gemini-3.1-pro` (orchestration), `claude-4.6-opus` (code + review), `gemini-2.5-flash` (simple). Budget caps per task complexity. |

---

## 6. How It Works (End-to-End)

### The Happy Path: Slack → Plan → Code → Ship

```
            PHASE 0                PHASE 1                PHASE 2
         ┌──────────┐          ┌──────────┐          ┌──────────┐
User     │  Slack    │  inbox/  │ Agent 08  │  consult │  Leads   │
@mention─▶│ Listener ├────────▶│  Loads    ├─────────▶│ Assess   │
         │ (daemon) │  .md     │  Context  │  (1 call │ (1 call  │
         └──────────┘  trigger │  Plans    │  each)   │  each)   │
                               │  (1 API   │          └────┬─────┘
                               │   call)   │               │
                               └──────────┘          ┌─────▼─────┐
                                                     │ Consensus │
            PHASE 5                PHASE 4            │ Check     │
         ┌──────────┐          ┌──────────┐          │ (0 calls) │
QA       │  Code    │  submits │  Workers  │  assigns └─────┬─────┘
Reviews◀─┤  Review  │◀────────┤  Write    │◀────────────────┘
(1 call) │  (Lead)  │         │  Code     │          PHASE 3
         │  (1 call)│         │  (3-8     │       ┌──────────┐
         └────┬─────┘         │   calls)  │       │  PM Sets │
              │               └──────────┘       │  Sprint  │
              ▼                                   │ (0 calls)│
         ┌──────────┐                             └──────────┘
         │  QA Gate │
         │  (1 call)├──PASS──▶ Git Commit (local) ──▶ DONE
         │          │
         └──────────┘
```

### Step-by-Step

1. **Trigger (Phase 0):** User tags `@Dream Team Agents` in Slack. The `slack_listener.py` daemon intercepts the event via WebSocket, verifies the workspace ID, and drops a `.md` trigger file into `context-store/inbox/`.

2. **Chief Wakes (Phase 1):** `agi_orchestrator.py` polls the inbox every 10 seconds. It finds the trigger, loads Agent 08's `SKILL.md`, reads `context_progress.md` (local file, 0 API calls), classifies the request with `RequestClassifier` (deterministic, 0 API calls), and makes **1 LLM call** to produce a structured execution plan.

3. **Lead Consultation (Phase 2):** The orchestrator spawns relevant department leads. Each lead reads the plan (local file), reads their department's context (local file), and makes **1 LLM call** to assess feasibility. The `ConsensusChecker` (deterministic, 0 API calls) verifies all leads agree.

4. **Sprint Setup (Phase 3):** PM (Agent 02) is fully deterministic. `SprintDecomposer` (topological sort) sequences tasks into sprints. `TemplateEngine` fills Trello card templates. Cards created via Trello API. **0 LLM calls.**

5. **Execution (Phase 4):** Workers read requirements from their notebooks (local file), fill approach proposals using templates (0 API calls, auto-approved if no concerns), then write code using **3-8 LLM calls** per task.

6. **Review (Phase 5):** Leads review worker output (**1 LLM call** per review). QA reviews for correctness and security (**1 LLM call**). Pass → Git Guardian allows local commit. Fail → rework cycle.

7. **Completion:** PM generates a sprint summary (template, 0 API calls). Chief validates final output against the original request (**1 LLM call**). Updates `context_progress.md` so the next session starts with full context.

---

## 7. LLM Routing & Inference-Minimal Protocol

### The Three-Phase Protocol

Every agent follows this exact sequence:

| Phase | What Happens | API Calls |
|-------|-------------|-----------|
| **1. Local Context Loading** | Read `context_progress.md`, own notebooks, source files, Trello cards | **0** |
| **2. Deterministic Decisions** | Routing, budgets, sprint decomposition, template fills, status updates | **0** |
| **3. LLM Call (only when needed)** | Strategic planning, code writing, code review, conflict resolution | **1-8** |

### Model Configuration (`coconutos.yml`)

```yaml
inference:
  mode: "api"                              # "api" | "hybrid" | "local"

  api:
    default_orchestration: "gemini-3.1-pro"  # Chief (Agent 08)
    default_code: "claude-4.6-opus"          # Workers (code generation)
    default_review: "claude-4.6-opus"        # Leads (code review)
    default_simple: "gemini-2.5-flash"       # Simple queries

  local:
    ollama_host: "http://localhost:11434"
    orchestration_model: "qwen2.5:7b-instruct-q4_K_M"
    code_model: "deepseek-coder-v2:6.7b-instruct-q4_K_M"

  budgets:
    max_calls_per_simple_task: 12
    max_calls_per_medium_task: 25
    max_calls_per_large_task: 60
    warn_at_percent: 80
```

### Per-Role Inference Profiles

| Role | Local Reads | LLM Calls | Purpose of LLM Call |
|------|-------------|-----------|---------------------|
| Agent 08 (Chief) | context, projects, sprint, git log | 1-3 | Plan production, output validation, mediation |
| Agent 02 (PM) | context, plan, events | **0** | Fully deterministic (templates + sorts) |
| Leads (05, 04, 06...) | context, plan, source files | 1-2 | Assessment, code review |
| Workers (05w, 04w...) | requirements, context, source | 3-8 | Code writing (irreducible core) |
| QA (10, 10w) | acceptance criteria, test results | 1 | Correctness + security review |
| Sentinels (11, 12) | file system, event bus | **0** | Fully deterministic (git blocking, alerts) |

---

## 8. Deterministic Decision Engine

Code that replaces LLM calls for routing decisions. Zero API cost.

| Module | File | Input | Output | What It Replaces |
|--------|------|-------|--------|-----------------|
| `RequestClassifier` | `request_classifier.py` | Raw text + project state | Request type (NEW / CONTINUATION / QUESTION) | LLM classification call |
| `ConsensusChecker` | `consensus_checker.py` | Lead assessments (JSON) | PROCEED / PROCEED_WITH_REFINEMENTS / CHIEF_DECIDES | LLM consensus call |
| `SprintDecomposer` | `sprint_decomposer.py` | Task list + dependency graph | Ordered sprints (topological sort) | LLM task sequencing call |
| `ApproachAutoApprover` | `approach_auto_approver.py` | Worker proposal | Approved / Needs Review | LLM approval call |
| `ContextProgressWriter` | `context_progress_writer.py` | Event data | Updated context_progress.md | LLM summarization call |
| `TemplateEngine` | `template_engine.py` | Structured data | Proposals, summaries, Trello cards | LLM document generation |

---

## 9. Template Engine

Templates replace LLM calls for all predictable structured outputs. Four templates are currently implemented in `template_engine.py`:

1. **Worker Approach Proposal** — Task understanding, proposed approach, files to touch, tests to write, questions/concerns (if empty → auto-approved)
2. **Lead → Worker Requirements Handoff** — Task spec, approved approach, patterns to follow, edge cases, budget limits, definition of done
3. **Sprint Summary** — Tasks completed, QA results, budget breakdown by agent, blockers, context for next sprint
4. **Trello Card** — Title with ticket ID, labels, checklist items from acceptance criteria, dependencies

---

## 10. Autonomy Model

### The Autonomy Ladder

| Level | Who Decides | Examples |
|-------|------------|---------|
| **3: SHREY REQUIRED** | System pauses | Budget > $50, scope change, 3rd QA fail, external deploys |
| **2: CHIEF** (Agent 08) | Logged decision | Dept selection, sprint count, tie-breaking, reassignment |
| **1: LEAD** | Domain authority | Spawn worker vs self-handle, task splits (max 3), approach selection |
| **0: WORKER** | Task boundaries | Implementation choices, file structure, test strategy, posting updates |

---

## 11. Governance & Security (Constitution v4)

### Twelve Immutable Rules

| # | Rule | Enforcement |
|---|------|-------------|
| 1 | **Org Hierarchy** | AutonomyGate middleware blocks unauthorized actions |
| 2 | **Context Loading** | Agent 08 must read 5 files before any planning |
| 3 | **Discussion-Before-Code** | Code-write tools BLOCKED until ApproachApprovalEvent exists |
| 4 | **Notebook Protocol** | Agents can only WRITE to own notebook, READ all |
| 5 | **Slack Communication** | EventBus → SlackProjection maps events to correct channels |
| 6 | **Trello** | Only PM (02) creates/moves cards; others can comment |
| 7 | **Git — LOCAL ONLY** | `push/pull/fetch/remote/clone` blocked at system call level |
| 8 | **Network — READ ONLY** | Outbound POST/PUT/PATCH/DELETE blocked except Slack/Trello/LLM |
| 9 | **No Freelancing** | Workers cannot create new tasks; must go through lead → PM |
| 10 | **QA Gate** | TaskCompleted without QAPassedEvent → commit BLOCKED |
| 11 | **Emergency Escalation** | Worker→Lead (2min) → Chief (5min) → Shrey (#emergency) |
| 12 | **Cost Governance** | 80% → warning, 95% → pause, 100% → hard stop |

### Personal Notebooks

Every agent maintains a notebook at `~/.gemini/antigravity/notebooks/agent-{id}/`:

```
├── progress.md       ← Running log of what I did
├── decisions.md      ← Decisions I made and why
├── requirements.md   ← Specs I'm working from
├── blockers.md       ← What's blocking me
├── ideas.md          ← Initiative ideas (not acted on — ticket first)
└── scratch/          ← Temporary working files
```

---

## 12. Observability Stack

Runs via Docker Compose (`docker-compose.yml`):

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| **Prometheus** | `prom/prometheus:latest` | 9090 | Scrapes metrics from orchestrator `:8000` |
| **Grafana** | `grafana/grafana:latest` | 3000 | Dashboards (login: admin/admin) |
| **Jaeger** | `jaegertracing/all-in-one:latest` | 16686 | Distributed tracing (OTLP on 4317/4318) |

### Metrics Exported (Prometheus)

- `dreamteam_llm_calls_total` — per agent, per model
- `dreamteam_budget_spent_usd` — running cost
- `dreamteam_tasks_completed_total` — task completions
- `dreamteam_agent_status` — per-agent state (idle/executing/blocked)
- `dreamteam_tokens_used_total` — token consumption

### Alert Monitor (`alert_monitor.py`)

- Tracks budget burn rate → warns at 80%, pauses at 95%
- Detects stuck agents (no heartbeat in 5 minutes) → Slack alert
- Posts to `#alerts` channel with agent identity

---

## 13. Custom Dashboard

A production-grade real-time web dashboard at **http://localhost:5050**.

### Design System
- **Typography:** DM Sans (UI) + JetBrains Mono (data/code)
- **Themes:** Light mode (warm beige) + Dark mode (charcoal). Toggle in sidebar.
- **Layout:** Left sidebar (navigation) + Tab bar (multi-project) + Content area

### Features
- **Silent Refresh:** Only fetches `/api/state` JSON every 3 seconds. No asset/CSS/HTML reloads. Cache-Control headers enforce this.
- **KPI Cards:** Active Agents, Total Cost, Burn Rate, API Calls
- **Agent Status Table:** Pulsing live dots, status badges (IDLE/WATCHING/EXECUTING), usage bars, per-agent cost & token counts
- **Budget Utilization Bar:** Gradient fill with shimmer animation. Auto-switches to red at >80%.
- **Recent Events Timeline:** Sourced from agent notebook file modifications (last 25 entries)
- **⌘K Command Bar:** Quick search (future: agent commands)
- **Sidebar:** Dashboard, Agents, Event log, Budget, Security, Slack, Trello, Ollama

### API Endpoint

`GET /api/state` returns:
```json
{
  "project": { "name": "...", "status": "IDLE|EXECUTING|MONITORING", "elapsed": "..." },
  "kpi": { "active_agents": 3, "total_cost": 0.0, "burn_rate": 0.0, "llm_calls": 0, ... },
  "agents": [{ "id": "08", "name": "Chief Orchestrator", "status": "IDLE", "cost": 0.0, ... }],
  "events": [{ "time": "23:54", "agent": "04", "message": "Updated decisions.md" }]
}
```

---

## 14. Setup Guide (OS-Agnostic)

### Prerequisites

1. **Python 3.10+** with pip
2. **Docker Desktop** (optional — only for Grafana/Prometheus/Jaeger)

### Step 1: Clone & Install

```bash
git clone <repository-url>
cd dream-team-v2
pip install -r requirements.txt
```

**Dependencies:** `google-genai`, `anthropic`, `slack_bolt`, `prometheus_client`, `opentelemetry-api`, `opentelemetry-sdk`, `python-dotenv`, `pyyaml`, `certifi`, `requests`

### Step 2: Configure `.env`

```env
GEMINI_API_KEY=your_gemini_key
CLAUDE_API=your_anthropic_key
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
TRELLO_API_KEY=your_trello_key
TRELLO_TOKEN=your_trello_token
```

### Step 3: Run

```bash
# Boot agents (Slack Listener + Orchestrator)
python3 coconutos_runner.py

# Boot observability (requires Docker)
docker compose up -d

# Boot dashboard
python3 dashboard_server.py
```

---

## 15. Environment Variables

| Variable | Required | Source | Used By |
|----------|----------|-------|---------|
| `GEMINI_API_KEY` | Yes | Google AI Studio | `llm_gateway.py`, `agi_orchestrator.py` |
| `CLAUDE_API` | Yes | Anthropic Console | `llm_gateway.py` |
| `SLACK_BOT_TOKEN` | Yes | Slack App Config (`xoxb-`) | `slack_worker.py`, `agi_orchestrator.py` |
| `SLACK_APP_TOKEN` | Yes | Slack App Config (`xapp-`) | `slack_listener.py` |
| `TRELLO_API_KEY` | Yes | Trello Power-Up Admin | `trello_worker.py` |
| `TRELLO_TOKEN` | Yes | Trello REST API | `trello_worker.py` |

---

## 16. Running the Stack

### Quick Commands

| Action | Command |
|--------|---------|
| Start agents | `python3 coconutos_runner.py` |
| Start observability | `docker compose up -d` |
| Start dashboard | `python3 dashboard_server.py` |
| Stop agents | `Ctrl+C` in runner terminal, or `pkill -f "agi_orchestrator\|slack_listener"` |
| Stop observability | `docker compose down` |
| Kill zombie processes | `pkill -f "agi_orchestrator.py\|slack_listener.py\|coconutos_runner.py"` |
| View metrics | `http://localhost:9090` (Prometheus) |
| View dashboards | `http://localhost:3000` (Grafana) or `http://localhost:5050` (Custom) |
| View traces | `http://localhost:16686` (Jaeger) |

---

## 17. Build Progress & Phases

### ✅ Phase 1: File Structure & Core Framework
Initialized 31 `SKILL.md` persona files, deployed Constitution v3, created persistent notebooks for all agents, established `context-store/` and `project-tracker/` directories.

### ✅ Phase 2: Slack Outbound
Built Slack bridge for agents to post messages as distinct bot identities. Injected identity config into all 31 SKILL.md files. E2E tested from Agent 08 → `#leadership`.

### ✅ Phase 3: Trello Integration
Secured API keys in `.env`. Queried live Trello board, mapped list IDs to `kanban.md`. Built Trello utility wrapping create/move/comment operations.

### ✅ Phase 4: Slack Inbound + AGI Orchestrator
Built `slack_listener.py` (Socket Mode). Created `context-store/inbox/` pipeline. **Major pivot:** Built headless AGI Orchestrator using Gemini API — intercepts inbox, loads SKILL.md, runs Chief Planning, executes recursive `[HANDOFF: xx]` loop for autonomous worker spawning.

### ✅ Phase 4.3: OS-Agnostic Refactor
Replaced macOS-specific `.plist` daemons and `.sh` shell scripts with cross-platform Python modules. Created `coconutos_runner.py` (universal process supervisor), `slack_worker.py`, and `trello_worker.py`. Refactored all hardcoded paths to use `os.path` dynamic resolution. Regenerated all 31 SKILL.md files with Python execution triggers.

### ✅ Phase 5: Handoff & Governance
Standardized Agent-to-Agent handoff protocol in Constitution. Built `sweep_notebooks.py` for cross-notebook state harvesting.

### ✅ Phase 6: Inference-Minimal Protocol
Built all deterministic modules (RequestClassifier, ConsensusChecker, SprintDecomposer, ApproachAutoApprover). Built Template Engine, Context Progress Writer, and multi-provider LLMGateway with Ollama support.

### ✅ Phase 7: Observability Stack
Prometheus metrics endpoint on `:8000`. Jaeger tracing. Grafana dashboards via Docker Compose. AlertMonitor for budget burn and stuck agent detection.

### ✅ Phase 8: Custom Real-Time Dashboard
Built `dashboard_server.py` + `dashboard.html`. Production SPA with DM Sans / JetBrains Mono design system. Silent JSON-only refresh (3s polling). Light/dark mode. Sidebar navigation, KPI cards, agent table, budget bar (shimmer), event timeline, ⌘K command bar.

---

## 18. Call Budget Economics

### Simple Task (1 sprint, 1 department, 1 worker)
```
08 inference: 1 + lead assessment: 1 + worker code: 3-5
  + lead review: 1 + QA review: 1 + 08 validation: 1
= 8-10 total calls (was 17-22 in v4.1, ~55% savings)
```

### Medium Task (1 sprint, 2 departments, 2 workers)
```
08 inference: 1 + 2 leads: 2 + 2 workers: 6-10
  + 2 lead reviews: 2 + 2 QA: 2 + 08 validation: 1
= 14-18 total calls (was 30-40, ~55% savings)
```

### Large Task (3 sprints, 3+ departments)
```
08 inference: 1 + 3 leads: 3
  + per sprint: [workers: 6-10 + reviews: 3 + QA: 3] × 3
  + 08 validation: 3
= 40-55 total calls (was 80-110, ~50% savings)
```

### Where Every Remaining Call Goes

| Call Type | Who | Why It Can't Be Eliminated |
|-----------|-----|---------------------------|
| Strategic inference | Agent 08 | Deciding WHAT to build requires reasoning |
| Lead assessment | Leads | Evaluating technical soundness needs judgment |
| Implementation | Workers | Writing code IS the LLM's core value |
| Code review | Leads | Finding bugs needs judgment |
| QA review | QA | Security/correctness needs reasoning |
| Output validation | Agent 08 | Comparing built vs. asked needs reasoning |

Everything else is a file read, template fill, or deterministic computation.

---

## 19. Local Model Migration Path

| Phase | Mode | Local % | API % | Requirement |
|-------|------|---------|-------|-------------|
| **1 (NOW)** | `api` | 0% | 100% | Cloud API keys. Templates reduce call count by 50%. |
| **2** | `hybrid` | 70% | 30% | Ollama installed. Simple/orchestration → local Qwen/Phi. Complex code → Claude. |
| **3** | `local` | 95% | 5% | When 7B models match Sonnet on code, or 32GB+ RAM. |
| **4** | `appliance` | 100% | 0% | Dedicated hardware (NUC + RTX 4090). Zero API dependency. |

Supported local models (M1 Pro 16GB, 4-bit quantized):
- Qwen 2.5 7B (~4.8 GB) — orchestration + review
- DeepSeek-Coder 6.7B (~4.2 GB) — code generation
- Phi-3 Mini 3.8B (~2.5 GB) — simple tasks

---

## 20. Future Roadmap

- [ ] **E2E Slack trigger test** — Full pipeline observation with live task execution
- [ ] **Grafana auto-provisioning** — Pre-configured dashboard JSON import on first boot
- [ ] **Dashboard: Task Pipeline** — Per-task status tracking (done/active/waiting) with spinning indicators
- [ ] **Dashboard: Multi-project tabs** — Wired to real project data
- [ ] **Dashboard: WebSocket upgrade** — Sub-second push updates replacing 3s polling
- [ ] **Per-agent cost attribution** — Break down spend by Gemini vs Claude provider
- [ ] **Production hardening** — Rate limiting, retry logic, circuit breakers on LLM calls
- [ ] **CoconutOS Appliance** — Dedicated local hardware, zero cloud dependency

---

*This document supersedes all previous documentation. For the detailed v4.2 protocol specification with code examples, see `ARCHITECTURE_V4_UNIFIED.md`.*

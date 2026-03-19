# 🥥 CoconutOS Dream Team v4.3 - Setup Guide

This guide explains how to set up the **Dream Team** virtual organization on any operating system (macOS, Windows, or Linux).

## 📋 Prerequisites

1.  **Python 3.10+** installed.
2.  **Pip** installed.
3.  **Docker Desktop** (optional, but required for Phase 7 Observability metrics).

## 🚀 Quick Start

### 1. Clone & Configure
```bash
git clone <repository-url>
cd dream-team-v2
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```
*(Requirements: google-genai, anthropic, slack_bolt, prometheus_client, opentelemetry-api, opentelemetry-sdk, python-dotenv, pyyaml, certifi)*

### 3. Setup Environment Variables
Create a `.env` file in the project root:
```env
GEMINI_API_KEY=your_key_here
CLAUDE_API=your_key_here
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
TRELLO_API_KEY=...
TRELLO_TOKEN=...
```

### 4. Running the Stack
To boot the entire organization (Slack Listener + AGI Orchestrator) in the background:
```bash
python coconutos_runner.py
```

## 🛠️ Components

- **`coconutos_runner.py`**: The unified entry point. It spawns and monitors background services.
- **`agi_orchestrator.py`**: The "Brain" that processes Slack triggers and executes agent handoffs.
- **`slack_listener.py`**: Listens for @mentions in authorized Slack workspaces and creates inbox tasks.
- **`coconutos.yml`**: Configures hybrid model routing (Gemini vs Claude vs Local Ollama).

## 📊 Observability (Optional)
If Docker is installed, run the monitoring stack:
```bash
docker compose up -d
```
- **Grafana**: `http://localhost:3000` (admin/admin)
- **Jaeger**: `http://localhost:16686`
- **Prometheus**: `http://localhost:9090`

## 🛡️ Security
- Ensure your `.env` is never committed.
- All agent operations are logged in `~/ .gemini/antigravity/notebooks/`.
- Git operations are blocked by system rules for safety.

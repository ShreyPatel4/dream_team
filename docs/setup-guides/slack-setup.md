# Slack Workspace Setup Guide

## Step 1: Create Workspace
Create a new Slack workspace (e.g., `shrey-dream-team.slack.com`)

## Step 2: Create Channels
```
#leadership        — Strategic decisions, cross-dept coordination
#eng-data          — Data engineering department
#eng-swe           — Software engineering department
#ops-infra         — Operations and infrastructure
#security          — Red team and security
#qa                — Quality assurance
#research          — Research and experiments
#product           — Product and project management
#general           — Org-wide announcements
#alerts            — Automated alerts from Agent 12
#standup           — Daily async standups
#emergency         — Agent 8 ONLY (escalation to Shrey)
```

## Step 3: Configure Slack MCP in Antigravity

In Antigravity settings, add MCP server:
```json
{
  "mcpServers": {
    "slack": {
      "type": "url",
      "url": "https://mcp.slack.com/sse",
      "name": "slack-mcp"
    }
  }
}
```

## Step 4: Agent Identity Convention
Since all agents operate through one Slack connection, they identify themselves
in message prefix:

```
[Agent 08 | Chief Orchestrator] Sprint 3 kickoff: all leads post status in #standup
[Agent 5w2 | SWE Systems/Rust] Starting TICKET-SWE-42: risk-gate hot-swap demo
[Agent 12 | Alert Monitor] ALERT: Agent 4w has no notebook update in 2 sessions
```

## Step 5: Channel Membership Matrix

| Agent | #leadership | #eng-data | #eng-swe | #ops | #security | #qa | #research | #product | #general | #alerts | #standup | #emergency |
|-------|:-----------:|:---------:|:--------:|:----:|:---------:|:---:|:---------:|:--------:|:--------:|:-------:|:--------:|:----------:|
| 08 Chief | X | X | X | X | X | X | X | X | X | X | X | X |
| 01 PO | X | | | | | | | X | X | | X | |
| 01w Analyst | | | | | | | | X | X | | | |
| 02 PM | X | | | | | | | X | X | | X | |
| 02w Scrum | | | | | | | | X | X | | X | |
| 03 TL | X | X | X | | | | | | X | | X | |
| 03w Arch | | X | X | | | | | | X | | | |
| 04 Lead DE | X | X | | | | | | | X | | X | |
| 04w Sr DE | | X | | | | | | | | | X | |
| 04w2 DQ | | X | | | | X | | | | | X | |
| 05 Lead SWE | X | | X | | | | | | X | | X | |
| 05w Backend | | | X | | | | | | | | X | |
| 05w2 Systems | | | X | | | | | | | | X | |
| 05w3 Frontend | | | X | | | | | | | | X | |
| 06 Lead Ops | X | | | X | | | | | X | | X | |
| 06w DevOps | | | | X | | | | | | | X | |
| 06w2 MLOps | | | | X | | | | | | | X | |
| 06w3 GPU | | | | X | | | | | | | X | |
| 07d CISO | X | | | | X | | | | X | X | X | |
| 07a Analysts | | | | | X | | | | | | X | |
| 07b Compliance | | | | | X | | | | | | X | |
| 07c Tester | | | | | X | X | | | | | X | |
| 07w Automation | | | | | X | | | | | | X | |
| 09 Research | X | | | | | | X | | X | | X | |
| 09w Res Eng | | | | | | | X | | | | X | |
| 10 QA Lead | X | | | | | X | | | X | | X | |
| 10w QA Eng | | | | | | X | | | | | X | |
| 10w2 QA Auto | | | | | | X | | | | | X | |
| 11 Git Guard | | | | | | X | | | | X | | |
| 12 Alert Mon | X | | | | | | | | | X | | |
| **Shrey** | X | X | X | X | X | X | X | X | X | X | X | X |

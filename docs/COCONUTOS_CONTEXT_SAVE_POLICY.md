# CoconutOS — Context Save Policy

**Version:** 1.0 · **Effective:** 2026-03-18 · **Enforcement:** Agent 00 (post-action hook)

> Every agent action produces a context dump. No exceptions. If it happened, it's on disk.

---

## 1. Filename Convention

```
<agent_name>_<id>_<project_name>_<timestamp>_context_progress_audit_log.md
```

**Examples:**
```
chief_orchestrator_08_data-kitchen_20260318_195030_context_progress_audit_log.md
sr_swe_backend_05w_data-kitchen_20260318_195215_context_progress_audit_log.md
project_manager_02_data-kitchen_20260318_200000_context_progress_audit_log.md
```

**Naming rules:**
- `agent_name`: lowercase, underscores (from SKILL.md `name` field)
- `id`: agent ID (08, 05w, 02, etc.)
- `project_name`: active project slug (lowercase, hyphens)
- `timestamp`: `YYYYMMDD_HHMMSS` in local time
- Suffix is always `_context_progress_audit_log.md`

---

## 2. Trigger Policy

**Trigger:** EVERY agent action. No exceptions.

An "action" is defined as:
- LLM inference call (start, complete, or failed)
- File read or write
- Slack message sent or received
- Trello card created, moved, or commented
- Agent spawned, killed, or status change
- Notebook update
- Handoff to another agent
- Alert fired
- Any deterministic module execution (classifier, decomposer, template, etc.)

---

## 3. Storage Path

```
context-dumps/<agent-name>/YYYY-MM-DD/<filename>
```

**Examples:**
```
context-dumps/chief-08/2026-03-18/chief_orchestrator_08_data-kitchen_20260318_195030_context_progress_audit_log.md
context-dumps/swe-05w/2026-03-18/sr_swe_backend_05w_data-kitchen_20260318_195215_context_progress_audit_log.md
context-dumps/pm-02/2026-03-18/project_manager_02_data-kitchen_20260318_200000_context_progress_audit_log.md
```

Directory structure is auto-created by the context dump writer.

---

## 4. Dump Schemas

### 4a. Chief Schema (Agent 08)

```markdown
# Context Dump: Chief Orchestrator (08)
## Timestamp: YYYY-MM-DD HH:MM:SS
## Project: <project_name>
## Session ID: <trace_id>

### Current State
- Status: IDLE | PLANNING | EXECUTING | REVIEWING
- Active project: <name>
- Sprint: <number> (tasks done: X/Y)

### Action Performed
- Type: <action_type>
- Summary: <one_line>
- LLM model used: <model>
- Cost: $<amount>
- Duration: <ms>ms

### Plan State
- Tasks delegated: <count>
- Agents active: <list>
- Agents pending: <list>
- Blockers: <list or "none">

### Context Files Read
- <file1>: <summary>
- <file2>: <summary>

### Decisions Made
- <decision1>: <rationale>

### Next Action
- <what happens next>
```

### 4b. Worker Schema (Agents 05w, 04w, 05w2, 05w3, 04w2, 06w, 06w2, 06w3, 07a, 07b, 07c, 07w, 09w, 10w, 10w2, 01w, 02w, 03w)

```markdown
# Context Dump: <Agent Name> (<ID>)
## Timestamp: YYYY-MM-DD HH:MM:SS
## Project: <project_name>
## Ticket: <TICKET-DEPT-N>

### Current State
- Status: IDLE | CODING | TESTING | IN_REVIEW | BLOCKED
- Ticket: <ticket_id>
- Task: <task_title>

### Action Performed
- Type: <action_type>
- Summary: <one_line>
- Files touched: <list>

### Progress
- Acceptance criteria met: X/Y
- Tests passing: X/Y
- Estimated completion: <percentage>%

### Code Changes
- Files modified: <list>
- Lines added/removed: +X / -Y

### Blockers
- <blocker or "none">

### Next Action
- <what happens next>
```

### 4c. PM Schema (Agent 02)

```markdown
# Context Dump: Project Manager (02)
## Timestamp: YYYY-MM-DD HH:MM:SS
## Project: <project_name>
## Sprint: <number>

### Current State
- Status: COORDINATING | SWEEPING | REPORTING
- Sprint: <number> (day X of Y)

### Action Performed
- Type: <action_type>
- Summary: <one_line>

### Sprint Health
- Tasks total: <N>
- In progress: <N> (agents: <list>)
- Blocked: <N> (blockers: <list>)
- In QA: <N>
- Done: <N>

### Agent Status
| Agent | Status | Last Dump | Stale? |
|-------|--------|-----------|--------|
| <id>  | <status> | <time_ago> | YES/NO |

### Kanban Sync
- Trello ↔ local drift: <count> discrepancies
- Action taken: <sync/escalate/none>

### Next Action
- <what happens next>
```

### 4d. Monitor Schema (Agent 12)

```markdown
# Context Dump: Alert Monitor (12)
## Timestamp: YYYY-MM-DD HH:MM:SS

### Action Performed
- Type: <health_check | alert_fired | sweep>
- Summary: <one_line>

### Org Health
- Status: GREEN | YELLOW | RED
- Active agents: <N>/<total>
- Stale agents: <list or "none">
- Open alerts: P0:<N> P1:<N> P2:<N>

### Alerts Fired This Session
- <ALERT-N>: <type> — <agent> — <detail>

### Budget
- Spent: $<amount> / $<limit> (<pct>%)
- Burn rate: $<rate>/min

### Next Check
- <timestamp>
```

---

## 5. Slack Identity Format

All agent Slack messages must use:
```
[Agent <N> | <Role>] <message>
```

Examples:
```
[Agent 08 | Chief Orchestrator] Planning phase complete for data-kitchen.
[Agent 02 | Project Manager] #standup: 3 in-flight, 1 blocked, 2 in QA.
[Agent 12 | Alert Monitor] P1: Agent 05w stale for 18m.
```

---

## 6. PM Sweep Triggers

Agent 02 (PM) health check sweep fires on three triggers:

| Trigger | Source | Frequency |
|---------|--------|-----------|
| **Chief explicit call** | Agent 08 issues `[HANDOFF: 02]` with sweep directive | On demand |
| **Cron timer** | Background thread in `pm_health_sweep.py` | Every 5 minutes |
| **Slack message received** | Any `slack_message_received` telemetry event | Per message |

Sweep output:
1. Reads all dumps in `context-dumps/`
2. Diffs timestamps against `stale_threshold_minutes` per agent
3. Reads `notebooks/<agent-name>/progress.md` for each active agent
4. Diffs against `kanban/state.json`
5. Posts standup to Slack `#standup`
6. Writes own context dump to `context-dumps/pm-02/YYYY-MM-DD/`

---

## 7. Agent 12 Stale Threshold

Agent 12 reads `stale_threshold_minutes` from each agent's `SKILL.md` frontmatter:

```yaml
---
stale_threshold_minutes: 10
dump_schema: worker
---
```

**Default thresholds by role:**

| Role | Threshold | Rationale |
|------|-----------|-----------|
| Chief (08) | 2 min | Brain of the org — must always be current |
| PM (02) | 5 min | Coordination hub — frequent updates expected |
| Monitor (12) | 2 min | Watchdog on the watchdog — must be live |
| Leads (01, 03–07d, 09, 10) | 10 min | Review cycles are longer but must stay engaged |
| Workers (all `w` agents) | 15 min | Deep work — longer intervals acceptable |
| Sentinels (00, 11) | 10 min | Background — less frequent but must be responsive |

If `now - last_dump_timestamp > stale_threshold_minutes`:
- Agent 12 fires **P1 alert**
- Posts to Slack `#alerts`: `[Agent 12 | Alert Monitor] P1: <agent> stale for <N>m`
- Logs to `audit-log/YYYY-MM-DD.md`

---

## 8. Enforcement

- **Agent 00** (Org Governance) runs the post-action hook. Every action → audit log line + context dump.
- **Agent 02** (PM) runs the health sweep. Every 5 min → staleness check + standup.
- **Agent 12** (Alert Monitor) watches `context-dumps/` for freshness. Stale → P1 alert.
- **All agents** have `## Context Save Protocol` in their SKILL.md with their specific `stale_threshold_minutes` and `dump_schema`.

This policy is immutable. Violations are logged and escalated.

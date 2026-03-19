# Dream Team v4 Unified — Orchestration Flow, Inference-Minimal Protocol & Hardened Constitution

**Coconut Labs · CoconutOS Agent Runtime**
**Version: 4.2 (merged)**

This is the single canonical reference for the Dream Team architecture. It merges the orchestration flow (v4.1), the inference-minimal protocol (v4.2), and the hardened constitution into one document. If something appears in an earlier v4/v4.1/v4.2 document but not here, this document takes precedence.

---

## Table of Contents

1. [Design Principles](#1-design-principles)
2. [The Central Context File](#2-the-central-context-file)
3. [Complete Orchestration Flow](#3-complete-orchestration-flow)
4. [Autonomy Model](#4-autonomy-model)
5. [Inference-Minimal Protocol](#5-inference-minimal-protocol)
6. [Template Engine](#6-template-engine)
7. [Deterministic Decision Engine](#7-deterministic-decision-engine)
8. [Hardened Constitution v4](#8-hardened-constitution-v4)
9. [Per-Role Inference Profiles](#9-per-role-inference-profiles)
10. [Local Model Migration Path](#10-local-model-migration-path)
11. [Call Budget Summary](#11-call-budget-summary)
12. [Implementation Checklist](#12-implementation-checklist)

---

## 1. Design Principles

Three rules govern every design decision in v4:

**1. Read locally, think locally, call API only for creative work.**
Every agent loads context from local markdown files and makes routing decisions through deterministic code. The LLM is called only when genuine reasoning, judgment, or code generation is needed.

**2. Every agent is a managed process with a budget, a heartbeat, and a kill switch.**
No agent runs unbounded. The runtime enforces token budgets, cost caps, rate limits, and wall-clock timeouts. Unresponsive agents are restarted. Runaway agents are killed.

**3. Context survives sessions. Context survives agent death.**
`context_progress.md` is updated at the end of every session. Every agent reads it at startup. If an agent dies mid-task, its working memory is persisted before termination. Zero context loss between sessions.

---

## 2. The Central Context File

`context-store/context_progress.md` is the single source of truth. Every agent reads it as a LOCAL FILE (zero API cost) before doing anything. It replaces the v4.1 pattern of "wake up, call LLM to understand what's going on."

### Structure

```markdown
# Project: [name]
## Status: [PLANNING | IN_SPRINT | BLOCKED | COMPLETE]
## Last Updated: [ISO timestamp]
## Updated By: [agent_id]

---

## Current State
[2-3 sentences: what exists right now in the codebase. Written by the last
agent to finish work. Plain English, no jargon.]

## What Was Just Completed
- [task_id]: [one-line description] by [agent_id] ([date])
- [task_id]: [one-line description] by [agent_id] ([date])

## What's In Progress
- [task_id]: [one-line description] assigned to [agent_id], status: [status]
  - Approach: [one-line summary of approved approach]
  - Files touched: [list of files]
  - Blockers: [none | description]

## What's Next (Ordered)
1. [task description] → [recommended department] → [estimated effort S/M/L]
2. [task description] → [recommended department] → [estimated effort S/M/L]

## Architecture Decisions (Append-Only Log)
- [date] [agent_id]: [decision]. Rationale: [why].

## Key Files
- `src/api/routes.py` — API endpoints (05w, last modified [date])
- `src/models/schema.py` — DB models (04w, last modified [date])
- `tests/` — test suite (10w, last modified [date])

## Sprint State
- Sprint: [N]
- Started: [date]
- Tasks total: [N], Done: [N], In progress: [N], Blocked: [N]
- Budget spent: $[X.XX] of $[Y.YY]
- Burn rate: $[X.XX]/min

## Dependencies & Blockers
- [none | description of what's blocking and who needs to unblock]

## Notes for Next Session
[Anything the last agent wanted the next agent to know. Free-form.]
```

### Rules

- **Who writes:** Agent 08 (at session end) or Agent 02 (after sprint updates). Workers don't write to it — leads summarize and update.
- **Who reads:** Every agent, at session start, as a local file read. No API call needed.
- **Format discipline:** Structured enough to parse programmatically. "What's Next" is an ordered queue — the next agent can read it and know what to do without asking an LLM.

---

## 3. Complete Orchestration Flow

This is the end-to-end lifecycle of a request, from trigger to delivery. Each phase marks which steps are **local file reads** (0 API calls), **deterministic code** (0 API calls), or **LLM calls** (costs money).

### Phase 0: Trigger

```
Input arrives (Slack mention | direct console | cron)
  │
  ▼
INTAKE DAEMON (always running)                          0 API calls
  • Receives event
  • Generates trace_id (propagated through entire lifecycle)
  • Normalizes into IncomingRequest
  • Drops into EventBus → wakes Agent 08
```

### Phase 1: Agent 08 Wakes — Context Loading

```
STEP 1.1 — Read Global State                           0 API calls
  • Read context-store/context_progress.md              ← file read
  • Read context-store/active_projects.json             ← file read
  • Read project-tracker/current_sprint.md              ← file read
  • Load own episodic memory (last 5 session summaries) ← file read

STEP 1.2 — Classify the Request                        0 API calls
  RequestClassifier (deterministic code):               ← code, not LLM
  • Keyword match against active project names
  • Check project status (IN_SPRINT → continuation, BLOCKED → unblock)
  • Question signals ("?", "what is", "how do") → QUESTION type
  • Agent escalation source → ESCALATION type
  • Default → NEW_PROJECT

STEP 1.3 — Deep Codebase Review (if continuation)      0 API calls
  • git log --oneline -20                               ← shell command
  • tree -L 2 of workspace directory                    ← shell command
  • Read key files from context_progress.md Key Files   ← file reads

STEP 1.4 — Produce Inference & Team Mapping             1 API call ★
  THIS is the one call that matters in Phase 1.
  Agent 08 has ALL context loaded locally. The LLM call is focused:
  "Given this project state, this codebase, and this request,
   produce a structured plan."

  Output (structured JSON):
  {
    "situation": "Pipeline is 60% built, DB schema done...",
    "next_steps": [
      {"description": "Complete API endpoints", "department": "eng-swe", "effort": "M"},
      {"description": "Add data validation", "department": "eng-data", "effort": "L"}
    ],
    "recommended_teams": {
      "primary": ["eng-swe", "eng-data"],
      "support": ["qa"],
      "review": ["security"]
    },
    "tasks": [...],                    // full task list with dependencies
    "task_dependencies": {...},        // dependency graph
    "estimated_sprints": 1,
    "estimated_cost_usd": 12.50,
    "requires_shrey_approval": false,
    "confidence": "high"
  }

  → Emit: ChiefInferenceReadyEvent
  → Agent 08 status: PLANNING
```

**Phase 1 total: 1 API call** (was 3 in v4.1).

### Phase 2: Lead Consultation — Parallel Negotiation

```
STEP 2.1 — Spawn Recommended Leads (not workers)       0 API calls
  Supervisor spawns only the leads named in 08's plan.  ← deterministic

STEP 2.2 — Each Lead Reviews Independently             1 API call per lead ★
  Each lead receives (all as local files):
  • 08's inference output                               ← file read
  • context_progress.md                                 ← file read
  • Their department's next_step items                  ← file read
  • Relevant source files                               ← file read

  Lead makes ONE LLM call to produce LEAD_ASSESSMENT:
  {
    "agree": true,
    "refinements": ["also need schema migration"],
    "effort": "L",
    "can_self_handle": true,
    "needs_workers": [],
    "approach": "Use Alembic for migration, add validation at model layer"
  }

  Lead posts summary in dept Slack + #leadership.

STEP 2.3 — Consensus Check                             0 API calls
  ConsensusChecker (deterministic code):                ← code, not LLM
  • All leads agree (with or without refinements) → PROCEED
  • Merge refinements into plan (append, no conflict)
  • Disagreement → CHIEF_DECIDES (08 gets 1 API call to mediate)
    But leads agree ~80% of the time, so this is rare.

STEP 2.4 — Cost/Scope Gate                             0 API calls
  Deterministic check:                                  ← arithmetic
  • estimated_cost > $50 → PAUSE for Shrey approval
  • scope_changed from original request → PAUSE for Shrey
  • Otherwise → PlanFinalizedEvent
```

**Phase 2 total: 1-2 API calls** (1 per lead consulted; was 3-4 in v4.1).

### Phase 3: PM Takes Over — Sprint Setup

```
STEP 3.1 — Sprint Decomposition                        0 API calls
  SprintDecomposer (deterministic code):                ← topological sort
  • ≤10 tasks → single sprint
  • Larger → multiple sprints by dependency order
  • Later sprints in BACKLOG until prior sprint passes QA

STEP 3.2 — Trello Board Population                     0 API calls
  Template engine fills Trello cards:                   ← template fill
  • Title: TICKET-DEPT-N: [task.title]
  • Labels: priority + department color
  • Assigned: department LEAD (not worker)
  • Checklist: acceptance criteria from plan
  • Dependencies: linked card IDs
  → Cards created via Trello API (not LLM API)

STEP 3.3 — Assignment Notifications                     0 API calls
  Template engine writes to each lead's requirements.md ← template fill
  SlackProjection posts in each dept channel             ← event bus
  PM enters MONITORING mode.

  → Emit: SprintStartedEvent
```

**Phase 3 total: 0 API calls** (was 2-3 in v4.1). PM is fully deterministic.

### Phase 4: Lead Autonomy — Spawn or Self-Handle

Each lead independently decides how to execute their assigned tasks. This is where the org hierarchy matters — leads have real authority.

```
Lead reads assigned Trello cards + requirements.md      0 API calls (file reads)

DECISION (per task):

  OPTION A: Self-Handle
    Conditions: task < 2hr, lead has context, no specialized sub-skill needed
    Flow: Lead executes directly → IN PROGRESS → IN REVIEW → QA GATE
    API calls: 0 for decision + lead's implementation calls (1-3) ★

  OPTION B: Spawn Worker
    Conditions: specialized skill needed, or task > 2hr, or lead is busy
    Flow:
    1. Lead writes DEEP instructions to worker's requirements.md  0 API calls
       (template from plan + LEAD_ASSESSMENT + architecture log)  ← template fill
    2. Supervisor.spawn(worker)                                   0 API calls
    3. Worker reads requirements.md                               0 API calls
    4. Worker fills approach proposal template                    0 API calls
       (auto-approved if no questions raised)                     ← deterministic
    5. Worker implements                                          3-8 API calls ★
    6. Lead reviews code                                          1 API call ★
    7. Lead submits to QA GATE

  OPTION C: Split & Distribute
    Conditions: task too large for one agent, parallelizable
    Flow:
    1. Lead decomposes into sub-tasks (max 3)                     0 API calls
    2. PM creates sub-task Trello cards                           0 API calls
    3. Each sub-task follows Option B independently

  Lead decision logged in decisions.md with rationale.            0 API calls
  Trello card updated with approach + assigned worker.            0 API calls
```

**Phase 4 decision overhead: 0 API calls.** Implementation calls depend on task complexity.

### Phase 5: Execution — Parallel, Monitored

```
WORKER EXECUTION LOOP (per worker):

  1. Read requirements.md → context loaded                0 API calls
  2. Fill approach proposal template                      0 API calls
     → Auto-approved if no concerns raised                ← deterministic
     → If concerns: lead reviews (1 API call)
  3. Implementation (the actual work):                    3-8 API calls ★
     • Each step = 1 LLM call through Gateway
     • Budget-checked before every call
     • Progress.md updated locally between calls
  4. If blocked:
     • Update blockers.md                                 0 API calls
     • Emit BlockedEvent → lead notified                  0 API calls
  5. If idea/concern mid-task:
     • STOP → write ideas.md → post in dept Slack         0 API calls
     • Lead reviews → approve/reject/escalate
  6. Task complete:
     • git commit (local only, conventional format)       0 API calls
     • Emit TaskCompletedEvent                            0 API calls

CONCURRENT RUNTIME MONITORING (background, not agents):
  • Heartbeat check every 30s                             0 API calls
  • Budget burn rate tracking                             0 API calls
  • Stuck detection (no progress in 5 min)                0 API calls
  • All visible on Grafana dashboard in real-time
```

### Phase 6: Code Review + QA Gate

```
STAGE 1: Lead Review                                    1 API call per task ★
  Lead reviews worker output (code diff, test results).
  Posts review in dept Slack.
  Changes needed → stays IN REVIEW, worker gets feedback.
  Approved → card moves to QA GATE.

STAGE 2: QA Gate                                        1 API call per task ★
  PM notifies QA Lead (10).
  QA assigns to QA Engineer (10w) or QA Automation (10w2).
  QA reads:
  • Acceptance criteria (from Trello card checklist)     ← file read
  • Source files to review                               ← file read
  • Test results (from running pytest locally)           ← shell command
  Then makes ONE LLM call to review for correctness + security.

  Security Tester (7c) runs in parallel:
  • Secret scanning                                      0 API calls (tooling)
  • Dependency vulnerability check                       0 API calls (tooling)

  QA OUTCOMES:
  PASS → Git Guardian permits commit → PM moves card → DONE
         → worker persists memory → IDLE → killed by Supervisor
  FAIL → bug card created → back to IN PROGRESS
         → 1st fail: normal rework
         → 2nd fail: lead must review before re-submit
         → 3rd fail: escalate to Chief → Shrey if needed
```

### Phase 7: Completion & Context Persistence

```
PM (02): Sprint Completion                              0 API calls
  • Template-generated sprint summary                    ← template fill
    (tasks, agents, times, costs, QA ratios — all from event bus data)
  • Posts summary in #leadership
  • Updates context_progress.md sprint section

CHIEF (08): Validation                                  1 API call ★
  • Compares delivered output vs. original request
  • If complete: marks project DONE, notifies Shrey
  • If multi-sprint: loads next sprint from BACKLOG,
    cycles back to Phase 4
  • Updates context_progress.md:
    - What was accomplished
    - Current codebase state
    - What's queued for next session

ALL AGENTS: Memory Persistence                          0 API calls
  • Working memory → committed to episodic storage
  • Key decisions → written to semantic memory (shared pool)
  • Notebooks synced from memory tiers
  • Idle workers → gracefully killed by Supervisor

RESULT: Next time Agent 08 is triggered, it reads
context_progress.md and KNOWS exactly where things stand.
Zero context loss between sessions.
```

---

## 4. Autonomy Model

When does the system act on its own, and when does it stop and ask Shrey?

### The Autonomy Ladder

```
LEVEL 3: SHREY REQUIRED (system pauses and waits)
─────────────────────────────────────────────────
• Project budget exceeds $50
• Scope change from original request
• Cross-department conflict that leads + chief can't resolve after 2 rounds
• Emergency escalation (system instability)
• Any action touching external services (deploy, publish)
• Hiring/firing agents (changing the org structure)
• Overriding a QA gate failure after 3 attempts

LEVEL 2: CHIEF AUTHORITY (Agent 08 decides, logs rationale)
──────────────────────────────────────────────────────────
• Which departments to involve
• Sprint count and sequencing
• Breaking a tie between disagreeing leads
• Reassigning work when an agent fails repeatedly
• Adjusting project-level budget allocation between teams
• Deciding to pause non-critical work to prioritize P0
• Activating emergency protocol

LEVEL 1: LEAD AUTHORITY (dept leads decide within their domain)
──────────────────────────────────────────────────────────────
• Spawn worker vs. self-handle decision
• Task decomposition within their department
• Technical approach selection for their domain
• Worker assignment (which worker gets which sub-task)
• Code review pass/fail within their department
• Correcting a worker's approach mid-task
• Splitting a task into sub-tasks (max 3)

LEVEL 0: WORKER AUTONOMY (workers act within task boundaries)
─────────────────────────────────────────────────────────────
• Implementation choices within approved approach
• File structure, naming, code organization
• Test strategy within coverage requirements
• Posting progress updates
• Flagging blockers (required, not optional)
• Writing to own notebook
```

### Runtime Enforcement

```python
class AutonomyGate:
    """Intercepts decisions and enforces the autonomy ladder.
    Runs as middleware on the EventBus."""

    async def check(self, event: Event, actor: AgentDescriptor) -> AutonomyDecision:
        # LEVEL 3: Requires Shrey
        if isinstance(event, BudgetApprovalRequest) and event.amount > 50.0:
            return AutonomyDecision.PAUSE_FOR_SHREY
        if isinstance(event, ScopeChangeEvent):
            return AutonomyDecision.PAUSE_FOR_SHREY
        if isinstance(event, QAOverrideRequest) and event.attempt_count >= 3:
            return AutonomyDecision.PAUSE_FOR_SHREY

        # LEVEL 2: Requires Chief
        if isinstance(event, CrossDeptAssignment) and actor.authority_level < 2:
            return AutonomyDecision.ESCALATE_TO_CHIEF
        if isinstance(event, AgentReassignment) and actor.authority_level < 2:
            return AutonomyDecision.ESCALATE_TO_CHIEF

        # LEVEL 1: Requires Lead
        if isinstance(event, ApproachProposalEvent) and actor.authority_level < 1:
            return AutonomyDecision.WAIT_FOR_LEAD_APPROVAL
        if isinstance(event, TaskSplitEvent) and actor.authority_level < 1:
            return AutonomyDecision.ESCALATE_TO_LEAD

        # LEVEL 0: Worker can proceed
        return AutonomyDecision.PROCEED
```

---

## 5. Inference-Minimal Protocol

### The Rule

Every agent follows three phases:

```
PHASE 1: LOCAL CONTEXT LOADING (0 API calls)
  1. Read context_progress.md
  2. Read own notebooks/agent-XX/progress.md
  3. Read own notebooks/agent-XX/requirements.md
  4. Read relevant source files (from Key Files section)
  5. Read Trello card description (cached locally)

  After this, the agent KNOWS: what the project is, what's been done,
  what they need to do, what approach was approved, what files to touch.

PHASE 2: DETERMINISTIC DECISIONS (0 API calls)
  Made by CODE, not LLM:
  • Task routing (role match + load scoring)
  • Budget checks (arithmetic)
  • Sprint decomposition (dependency graph sort)
  • Trello card creation (template fill)
  • Status updates (append to file)
  • Heartbeat + health checks
  • Alert detection (threshold comparison)
  • Notebook sweep (file aggregation)
  • Git operations (direct command)
  • Request classification (keyword match)
  • Consensus checking (JSON flag parsing)
  • Approach auto-approval (no concerns → approve)

PHASE 3: LLM CALL — ONLY WHEN NEEDED
  The ONLY things requiring an API call:
  • Agent 08: Producing inference (situation → plan + team mapping)
  • Leads: Reviewing an approach and deciding agree/disagree/refine
  • Workers: Actually writing code / implementing solutions
  • QA: Reviewing code for correctness and security issues
  • Agent 08: Validating final output against original request
  • Agent 08: Mediating lead disagreements (rare)
```

---

## 6. Template Engine

Templates replace LLM calls for all predictable structured outputs.

### Template: Worker Approach Proposal

```markdown
# Approach Proposal — [task_id]
## Agent: [agent_id] | [role]
## Task: [task title from Trello card]
## Date: [auto-filled]

## Understanding
[Copy from requirements.md: task description section]

## Proposed Approach
[Copy from requirements.md: approach section — lead already wrote this]

## Files I Will Touch
[Copy from requirements.md: file list]

## Tests I Will Write
[Copy from requirements.md: test requirements]

## Questions / Concerns
[Worker fills this — if empty, auto-approve. If non-empty, lead reviews.]

## Estimated Effort
[Copy from requirements.md: effort estimate]
```

Auto-approved if Questions/Concerns is empty. Only if non-empty does a lead need 1 API call.

### Template: Lead → Worker Requirements Handoff

```markdown
# Task Requirements — [task_id]
## For: Agent [worker_id] | [worker_role]
## From: Agent [lead_id] | [lead_role]
## Date: [auto-filled]

## What You're Building
[task.description from ExecutionPlan]

## Why
[task.rationale or lead's LEAD_ASSESSMENT.approach]

## Approach (Follow This)
[lead's LEAD_ASSESSMENT.approach — this IS the approved approach]

## Files to Touch
[From context_progress.md Key Files + lead's assessment]

## Patterns to Follow
[From context_progress.md Architecture Decisions section]

## Tests Required
[task.acceptance_criteria reworded as test specs]

## Edge Cases to Handle
[From lead's assessment, if any]

## When You're Done
1. Run all tests: `pytest tests/`
2. Update your progress.md
3. Commit: `type(scope): description [TASK_ID]`
4. Post in dept Slack: "task_id complete, ready for review"

## Budget
- Max tokens: [from ResourceGovernor allocation]
- Max cost: $[from ResourceGovernor allocation]
- Max time: [from ResourceGovernor allocation]
```

### Template: Sprint Summary

```markdown
# Sprint [N] Summary — [project name]
## Generated: [timestamp]
## Duration: [start] to [end]

## Tasks Completed
| Task | Agent | Started | Completed | Cost | Tokens |
|------|-------|---------|-----------|------|--------|
[rows from TaskCompletedEvent log]

## QA Results
- Total submissions: [from QARequestedEvent count]
- First-pass rate: [QAPassedEvent first attempt / total]
- Rework cycles: [QAFailedEvent count]

## Budget
- Allocated: $[sprint budget]
- Spent: $[ResourceGovernor totals]
- By agent: [per-agent breakdown]
- By model: [LLM Gateway breakdown]

## Blockers Encountered
[From BlockedEvent log, with resolution]

## Context for Next Sprint
[From context_progress.md "Notes for Next Session"]
```

### Template: Trello Card

```markdown
Title: [TICKET_ID]-[DEPT]-[N]: [task.title]
Labels: [task.priority] + [department.color]
Members: [department.lead_id]
Description: |
  ## Task Specification
  [task.description from ExecutionPlan]
  ## Acceptance Criteria
  [task.acceptance_criteria — checklist items]
  ## Context
  See: context_progress.md
  ## Dependencies
  [task.dependencies — linked card IDs]
Checklist: [task.acceptance_criteria as checkbox items]
```

---

## 7. Deterministic Decision Engine

Code that replaces LLM calls for routing decisions.

### Request Classification

```python
class RequestClassifier:
    """Deterministic. Zero API calls."""

    def classify(self, request: IncomingRequest, context: ProjectContext) -> RequestType:
        # Match against active projects
        if context.active_projects:
            for project in context.active_projects:
                if self._matches_project(request.raw_content, project):
                    if project.status == "IN_SPRINT": return RequestType.CONTINUATION
                    elif project.status == "BLOCKED":  return RequestType.UNBLOCK
                    elif project.status == "COMPLETE": return RequestType.NEW_PHASE

        # Question detection
        question_signals = ["?", "what is", "how do", "can you explain",
                           "tell me about", "what's the status"]
        if any(s in request.raw_content.lower() for s in question_signals):
            return RequestType.QUESTION

        if request.source == "agent_escalation":
            return RequestType.ESCALATION

        return RequestType.NEW_PROJECT

    def _matches_project(self, content: str, project: Project) -> bool:
        keywords = [project.name.lower()] + [t.lower() for t in project.keywords]
        return any(kw in content.lower() for kw in keywords)
```

### Consensus Check

```python
class ConsensusChecker:
    """Deterministic. Zero API calls."""

    def check(self, assessments: List[LeadAssessment]) -> ConsensusResult:
        all_agree = all(a.agree for a in assessments)
        has_refinements = any(a.refinements for a in assessments)

        if all_agree and not has_refinements:
            return ConsensusResult(reached=True, action="PROCEED")

        if all_agree and has_refinements:
            merged = [r for a in assessments for r in a.refinements]
            return ConsensusResult(reached=True, action="PROCEED_WITH_REFINEMENTS",
                                  merged_plan=merged)

        dissenters = [a for a in assessments if not a.agree]
        return ConsensusResult(reached=False, action="CHIEF_DECIDES",
                              dissenters=dissenters)
        # Chief 08 needs 1 API call to mediate — but leads agree ~80% of the time.
```

### Sprint Decomposition

```python
class SprintDecomposer:
    """Topological sort. Zero API calls."""

    def decompose(self, plan: ExecutionPlan, max_per_sprint: int = 10) -> List[Sprint]:
        sorted_tasks = self._topological_sort(plan.tasks, plan.task_dependencies)
        sprints, current = [], []

        for task in sorted_tasks:
            deps = plan.task_dependencies.get(task.id, [])
            deps_satisfied = all(
                any(t.id == dep for s in sprints for t in s) for dep in deps)

            if not deps_satisfied and current:
                sprints.append(current)
                current = []
            current.append(task)
            if len(current) >= max_per_sprint:
                sprints.append(current)
                current = []

        if current: sprints.append(current)
        return [Sprint(number=i+1, tasks=t) for i, t in enumerate(sprints)]
```

### Approach Auto-Approval

```python
class ApproachAutoApprover:
    """Zero API calls when approach matches."""

    def check(self, proposal: ApproachProposal, reqs: TaskRequirements) -> ApprovalDecision:
        if not proposal.questions_or_concerns:
            return ApprovalDecision(approved=True, method="auto",
                reason="Worker confirmed understanding, no concerns raised.")

        return ApprovalDecision(approved=False, method="needs_lead_review",
            reason=f"Worker raised {len(proposal.questions_or_concerns)} concerns.")
```

---

## 8. Hardened Constitution v4

These rules are enforced by the runtime, not by agent compliance.

### Rule 1: Organizational Hierarchy
The v3 hierarchy is unchanged. Authority levels are enforced by the AutonomyGate. A worker cannot commit code without a QA pass event. A lead cannot assign cross-department work without Chief approval.

### Rule 2: Context Loading Protocol
**On every Agent 08 activation (mandatory, before any planning):**
1. `context-store/context_progress.md` — project state
2. `context-store/active_projects.json` — all active projects
3. `project-tracker/current_sprint.md` — sprint state
4. Own episodic memory — last 5 session summaries
5. `git log --oneline -20` — recent code changes

**Conditional reads:**
- Continuation → workspace file tree + key source files
- New project → research agent (09) notebooks for prior art
- Escalation → blocking agent's notebooks + blockers.md

**On every Agent 08 session end (mandatory):**
1. Update `context_progress.md` — new project state
2. Update own `progress.md` — session log
3. Update own `decisions.md` — decisions + rationale
4. Episodic memory commit — structured session summary

### Rule 3: Discussion-Before-Code

Runtime-enforced. Code-writing tools are BLOCKED until `ApproachApprovalEvent` exists for the current task.

1. Worker reads requirements.md
2. Worker fills approach proposal template
3. Auto-approved if no concerns (0 API calls) OR lead reviews (1 API call)
4. ONLY AFTER approval: code_write tools unlocked
5. Attempt before approval → BLOCKED + AlertEvent

### Rule 4: Notebook Protocol
Same directory structure as v3. Notebooks are now a MIRROR of the memory subsystem:
- Write: Agent → Memory Tier → auto-sync → Notebook file
- Read: Agent → Memory Tier (primary) → Notebook (fallback if memory empty)
- Shrey edit: File watcher detects change → propagated back to memory tier

### Rule 5: Slack Communication
Events on the EventBus → SlackProjection translates to Slack messages with correct agent identity. Shrey's messages have priority=P0 and preempt agent work.

### Rule 6: Trello (PM-owned, bidirectional sync)
PM (02) is the only agent that creates/moves cards. Others can comment. If Shrey manually drags a card, TrelloBridge emits TaskStatusChangeEvent.

### Rule 7: Git — LOCAL ONLY
Runtime service intercepts git commands. `push/pull/fetch/remote/clone` blocked at system call level. Conventional commits with ticket reference. Secret scanning pre-commit.

### Rule 8: Network — READ ONLY
Outbound POST/PUT/PATCH/DELETE to non-localhost blocked by network proxy. Exceptions: Slack API, Trello API, LLM provider APIs (whitelisted).

### Rule 9: No Freelancing
AutonomyGate blocks TaskSplitEvent or new work creation from workers. Route: ideas.md → dept Slack → lead review → PM ticket if approved.

### Rule 10: QA Gate (mandatory, enforced)
- Git Guardian tracks which files each agent touched
- TaskCompletedEvent without prior QAPassedEvent → commit BLOCKED
- Failure escalation: 1st fail = rework; 2nd fail = lead reviews; 3rd fail = Chief → Shrey

### Rule 11: Emergency Escalation
- Worker blocked → Lead (2 min timeout)
- Lead can't resolve → Chief (5 min timeout)
- Chief can't resolve → Shrey (#emergency + Slack DM)
- Timeouts enforced by Alert Monitor (12) watching event bus

### Rule 12: Cost Governance
- Budget hierarchy: Project → Sprint → Task → Agent
- Every LLM call logged: agent_id, model, tokens, USD
- 80% consumed → warning to lead + Chief
- 95% consumed → work paused, Shrey notified
- 100% → hard stop, no exceptions

---

## 9. Per-Role Inference Profiles

How each role uses local files vs. API calls in steady state.

### Agent 08 (Chief Orchestrator)
```
LOCAL:  context_progress.md, active_projects.json, current_sprint.md, git log
API:    1 call — producing the inference (situation → plan + team mapping)
        1 call — validating final output vs. original request
        0-1 call — mediating lead disagreements (rare)
LOCAL:  writes context_progress.md, progress.md, decisions.md
```

### Agent 02 (PM)
```
LOCAL:  context_progress.md, ExecutionPlan, event bus data
API:    0 calls — PM is FULLY DETERMINISTIC
        Sprint decomposition = topological sort
        Trello cards = template fill
        Sprint summary = event aggregation
LOCAL:  writes Trello cards (Trello API), sprint summary, context_progress.md updates
```

### Leads (05, 04, 06, etc.)
```
LOCAL:  context_progress.md, 08's inference, team notebooks, source files
API:    1 call — LEAD_ASSESSMENT (judgment: agree/disagree/refine)
        0-1 call — reviewing worker approach (only if concerns raised)
        1 call per worker — code review (judgment)
LOCAL:  writes worker's requirements.md (template), own decisions.md
```

### Workers (05w, 04w, etc.)
```
LOCAL:  requirements.md, context_progress.md, source files, architecture log
API:    3-8 calls — writing code (the irreducible core)
LOCAL:  writes approach proposal (template), progress.md, code files
```

### QA (10, 10w)
```
LOCAL:  acceptance criteria, source files, test results (pytest output)
API:    1 call — reviewing code for correctness + security
LOCAL:  writes QA result (template: pass/fail + findings)
```

---

## 10. Local Model Migration Path

The Gateway abstracts the backend. Agents never know if they're talking to Claude, Ollama, or anything else.

### Hardware Reality: M1 Pro 16GB, 10-core GPU

```
WHAT FITS (4-bit quantized):
  Qwen 2.5 7B (Q4_K_M)     ~4.8 GB    — orchestration + review
  DeepSeek-Coder 6.7B (Q4)  ~4.2 GB    — code generation
  Phi-3 Mini 3.8B (Q4)      ~2.5 GB    — simple tasks
  Llama 3.1 8B (Q4_K_M)     ~5.0 GB    — general purpose

CONSTRAINT: One 7-8B model at a time. Swap takes ~3-8 seconds.
```

### Migration Phases

```
PHASE 1 (NOW): API-only
  All calls through cloud APIs. Templates + deterministic engine
  reduce calls by ~50%. Cost tracking validates savings.

PHASE 2 (AFTER STABLE): Hybrid
  Simple/orchestration → local Qwen 2.5 7B or Phi-3 Mini
  Complex code → API (Claude Sonnet for quality)
  Target: 70% local, 30% API.

PHASE 3 (BETTER MODELS): Full Local
  When 7B models match current Sonnet quality on code.
  OR 32GB+ hardware upgrade.
  Target: 95% local, 5% API.

PHASE 4 (COCONUTOS APPLIANCE): All Local
  Dedicated hardware (NUC + RTX 4090).
  13B-30B models. Zero API dependency.
  "AI engineering team in a box."
```

### Gateway Configuration

```yaml
# coconutos.yml
inference:
  mode: "api"  # "api" | "hybrid" | "local"

  api:
    default_orchestration: "claude-sonnet-4"
    default_code: "claude-sonnet-4"
    default_review: "claude-sonnet-4"
    default_simple: "gemini-2.0-flash"

  local:
    ollama_host: "http://localhost:11434"
    orchestration_model: "qwen2.5:7b-instruct-q4_K_M"
    code_model: "deepseek-coder-v2:6.7b-instruct-q4_K_M"
    review_model: "qwen2.5:7b-instruct-q4_K_M"
    simple_model: "phi3:mini-q4_K_M"
    context_window: 8192
    swap_timeout_seconds: 15

  budgets:
    max_calls_per_simple_task: 12
    max_calls_per_medium_task: 25
    max_calls_per_large_task: 60
    warn_at_percent: 80
```

---

## 11. Call Budget Summary

### Simple Task (1 sprint, 1 department, 1 worker)

```
08 inference: 1 + lead assessment: 1 + worker implements: 3-5
  + lead review: 1 + QA review: 1 + 08 validation: 1
TOTAL: 8-10 calls (was 17-22 in v4.1 — ~55% savings)
```

### Medium Task (1 sprint, 2 departments, 2 workers)

```
08 inference: 1 + 2 lead assessments: 2 + 2 workers: 6-10
  + 2 lead reviews: 2 + 2 QA reviews: 2 + 08 validation: 1
TOTAL: 14-18 calls (was 30-40 — ~55% savings)
```

### Large Task (3 sprints, 3+ departments)

```
08 inference: 1 + 3 lead assessments: 3
  + per sprint: [workers: 6-10 + reviews: 3 + QA: 3] × 3
  + 08 validation per sprint: 3
TOTAL: 40-55 calls (was 80-110 — ~50% savings)
```

### Where Every Remaining Call Goes

```
CALL TYPE              WHO        WHY IT CAN'T BE ELIMINATED
────────────────────   ─────      ──────────────────────────
Strategic inference    08         Deciding WHAT to build requires reasoning
Lead assessment        Leads      Evaluating technical soundness needs judgment
Implementation         Workers    Writing code IS the LLM's core value
Code review            Leads      Finding bugs needs judgment
QA review              QA         Security and correctness needs reasoning
Output validation      08         Comparing built vs. asked needs reasoning
Mediation (rare)       08         Resolving disagreements needs reasoning
```

Everything else is a file read, template fill, or deterministic computation.

---

## 12. Implementation Checklist

### Core Runtime (from v4)
- [ ] AgentDescriptor, AgentRuntime, EventBus
- [ ] Supervisor with spawn/kill/restart/health monitoring
- [ ] ResourceGovernor with budget enforcement
- [ ] LLMGateway with multi-provider routing
- [ ] Three-tier memory (Redis + SQLite/FAISS + persistent)

### Inference-Minimal Additions (from v4.2)
- [ ] `context_progress.md` writer — auto-updates at session end
- [ ] Template engine — approach proposals, sprint summaries, Trello cards, requirements handoffs
- [ ] RequestClassifier — deterministic, replaces LLM classification
- [ ] ConsensusChecker — deterministic, replaces LLM consensus
- [ ] SprintDecomposer — topological sort, replaces LLM decomposition
- [ ] ApproachAutoApprover — auto-approves when no concerns raised
- [ ] LLMGateway mode switch — `api` / `hybrid` / `local`
- [ ] Ollama provider — same interface as cloud providers
- [ ] Model swap manager — loading/unloading on constrained hardware
- [ ] Call counter — tracks API calls per session, per agent, per task type

### Observability Stack
- [ ] Prometheus metrics (agent status, tokens, cost, latency, restarts)
- [ ] OpenTelemetry tracing through Jaeger
- [ ] Grafana dashboards (agent overview, cost & budget, task pipeline)
- [ ] Alerting rules (budget warnings, stuck agents, restart loops)

### Integration Bridges
- [ ] Slack Projection (events → channels with agent identities)
- [ ] Trello Bridge (bidirectional sync)
- [ ] Git Bridge (local-only enforcement at system call level)

### Docker Compose Stack
- [ ] Runtime container
- [ ] Redis (working memory)
- [ ] Prometheus + Grafana
- [ ] Jaeger (traces)
- [ ] Ollama (optional, for local models)

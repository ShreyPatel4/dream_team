# Trello Board Setup Guide

## Step 1: Create Board
Create a Trello board per project (e.g., "risk-hotpath-hft", "Sepal AI")

## Step 2: Create Lists (in order)
```
1. BACKLOG         — Unscheduled work, ideas, future items
2. SPRINT N TODO   — Current sprint, assigned but not started
3. IN PROGRESS     — Active work
4. IN REVIEW       — Pending lead review
5. QA GATE         — Pending QA approval
6. BLOCKED         — Waiting on dependency/resolution
7. DONE            — Completed and committed
```

## Step 3: Label System
```
Colors:
  Red     = P0 (Critical/Blocking)
  Orange  = P1 (Important)
  Yellow  = P2 (Normal)
  Green   = P3 (Nice-to-have)
  
  Blue    = Engineering (SWE)
  Purple  = Data Engineering
  Cyan    = Ops/Infrastructure
  Pink    = Security
  Lime    = QA
  Gray    = Product/PM
```

## Step 4: Card Template
```
Title: TICKET-DEPT-NNN: Short description

Description:
  ## Context
  [Why this work exists]
  
  ## Requirements
  [What needs to be done]
  
  ## Acceptance Criteria
  - [ ] Criterion 1
  - [ ] Criterion 2
  
  ## Dependencies
  [Blocking/blocked-by tickets]

Checklist: "Acceptance Criteria" (mirrors description)
Members: Assigned agent(s)
Due Date: Sprint deadline
Labels: Priority + Department
```

## Step 5: Configure Trello MCP in Antigravity

Currently Antigravity doesn't have a native Trello MCP. Options:
1. Use Slack-Trello integration (Trello Power-Up in Slack)
2. Build a custom MCP server for Trello API
3. Use the filesystem-based project-tracker as fallback with Trello sync

Recommended: Start with Slack-Trello Power-Up. PM (Agent 2) creates/updates
cards via Slack commands: `/trello add`, `/trello move`, etc.

## Step 6: Automation Rules (Butler)
```
When a card is moved to "IN PROGRESS":
  → Add due date (sprint end)
  → Post to #general: "[PM] TICKET-XXX started by Agent N"

When a card is moved to "BLOCKED":
  → Post to #alerts: "BLOCKED: TICKET-XXX — [reason]"
  → Add red "BLOCKED" label

When a card is moved to "DONE":
  → Remove all members
  → Post to #general: "[PM] TICKET-XXX completed"
  → Check all items in checklist
```

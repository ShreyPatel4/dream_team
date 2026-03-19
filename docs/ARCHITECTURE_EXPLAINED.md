# How the Dream Team Framework Operates Under the Hood

The Dream Team v3 framework is a hybrid system that bridges your local file system, the Antigravity IDE, and external APIs (Slack/Trello) to simulate a living 31-person company. 

Here is exactly how the pieces interact systematically, from the moment you have an idea to the moment code is written and verified.

---

## 1. The Trigger: Slack Auto-Spawn
Unlike a traditional script that waits for you to type in a terminal, we gave the org "ears" using the `slack_listener.py` background daemon.

1. **The Daemon:** When you ran `start-dream-team.sh`, macOS started running the Python script silently in the background. It maintains an open, secure WebSocket connection to Slack using the `xapp-` App Token.
2. **The Event:** When you send `@Dream Team Agents` in Slack, Slack's servers push that event down the WebSocket directly to your Mac.
3. **The Interception:** Your `slack_listener.py` receives the event. It verifies the Workspace ID (`T0AL981MNP9`) to ensure it's not a malicious actor from another Slack instance.
4. **The Handoff Payload:** If verified, the Python script takes your message and writes it into a literal text file inside `~/.gemini/antigravity/context-store/inbox/`. It then fires a Mac push notification to wake you up.

## 2. The Boot: Antigravity IDE & The Chief
The "brains" of the agents only exist when you launch Antigravity and assign a specific persona.

1. **Assuming the Identity:** When you open Antigravity and say, "You are Agent 08 (Chief Orchestrator)", the IDE reads the massive `08-chief-orchestrator/SKILL.md` file we installed.
2. **The First Rule:** The absolute first rule in Agent 08's `SKILL.md` is to *scan the `inbox/` directory*.
3. **The Initiation:** Agent 08 reads the payload file dropped by the Slack daemon, deletes it from the inbox, and begins the Planning Phase. At this point, the system has successfully bridged Slack to your local IDE.

## 3. The Database: Trello & Kanban Coordination
Because there are 31 agents, they cannot share short-term memory inside Antigravity natively. We built an external "database" using your local file system and Trello.

1. **Task Tracking:** When Agent 08 creates a plan, it must format it into a "Ticket" (e.g., `TICKET-ENG-05`).
2. **Trello Bridge:** Agent 08 or PM (Agent 02) uses the `trello-tool.sh` bash script. They supply the ticket title and the list ID (e.g., `Backlog`). The tool hits the Trello REST API using your credentials in `.env` and creates a live Trello card. 
3. **The Local Sync:** Agents update `project-tracker/kanban.md` locally to mirror the Trello board so any agent can quickly read the state of the project without wasting API tokens.

## 4. The Assembly Line: Agent-to-Agent Handoffs
This is where the magic happens. Agents cannot "talk" directly to each other inside the IDE, so they communicate through notebooks and Slack.

1. **The Assignment:** Let's say Agent 05 (Lead SWE) wants Agent 05w (Backend Worker) to write code.
2. **The Notebook Drop:** Agent 05 navigates to `~/.gemini/antigravity/notebooks/agent-05w/requirements.md` and appends the exact technical specification for the code. This is the worker's "desk."
3. **The Slack Ping:** Agent 05 then executes `slack-bridge.sh`. It sends a message to the `#eng-swe` Slack channel stating: *"@Agent 05w I have deployed the requirements to your notebook. Begin development."*
4. **The Persona Shift:** You (the human) see the Slack message, tell Antigravity "You are now Agent 05w," and the IDE loads the new persona.
5. **The Execution:** The very first rule in Agent 05w's skill is to read its own notebook. It finds the requirements left by the Lead, reads them, and starts coding.

## 5. The Governance: Rules & Git Controls
An org of 31 autonomous agents could easily destroy a codebase or leak secrets. We built layers of security to prevent this.

1. **The Constitution:** Every single agent is forced to load `global-rules/rules.md`. This file outranks everything else. It tells them who their boss is, what Slack channels they are allowed in, and dictates that **Network access is READ-ONLY** (preventing them from making rogue POST requests to random servers).
2. **The Git Guardian (Agent 11):** The rules state that NO agent is allowed to run `git push`, `git pull`, or `git fetch`.
3. **The QA Gate (Agent 10):** A worker agent can write code, but they cannot commit it. They must move the Trello card to "QA Gate". You load Agent 10, the QA agent runs linters, security scans, and tests. Only if Agent 10 updates the Trello card to "APPROVED" does the Red Team (Agent 11) allow a local `git commit`. The code mathematically cannot leave your hard drive until you (the founder) explicitly push it yourself.

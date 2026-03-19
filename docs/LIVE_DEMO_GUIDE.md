# Live Demo Guide: Testing the Dream Team Org

Follow these steps exactly to run your first end-to-end "Live Action" trial of the 31-agent architecture.

## Phase 1: The Slack Initiation
1. Do not open Antigravity yet. 
2. Open Slack on your phone or laptop. Navigate to **Coconut Labs**.
3. Go into `#leadership` (or `#general`) and send the following exact message:
   > `@Dream Team Agents Let's build a simple Python script that pulls the current price of Bitcoin and logs it to a file. I want to see the whole team collaborate on this.`
4. **Observe:** Within 3 seconds, a native Mac notification will appear on your screen saying: *"Agent 08 Summoned via Slack! 🚨"*
5. *Behind the scenes: The background listener parsed the command securely, checked that you were inside Coconut Labs, and dropped a payload into `context-store/inbox/` waiting for the Chief.*

## Phase 2: Agent Boot-Up
1. Now, open Google Antigravity IDE.
2. Tell the Agent: *"You are Agent 08, check your inbox."*
3. **Observe:** The agent will automatically assume the persona of the Chief Orchestrator, read the `inbox/` payload that Slack just created, and acknowledge the Bitcoin script project.

## Phase 3: The Council Plans
1. Agent 08 will analyze the request. It knows it is a new project.
2. Instruct Agent 08: *"Consult the council and produce the scope document."*
3. **Observe:** Agent 08 reads the `notebooks` belonging to Agent 03 (Tech Lead) and Agent 01 (Product). They agree to use `requests` and a simple `.txt` logging structure.
4. Instruct Agent 08: *"Write the Trello Tickets to the Kanban tracker."*
5. **Observe:** Let it modify `kanban.md`. The Trello Bridge tool (`trello-tool.sh`) automatically fires REST API commands moving Trello cards into the live Backlog.

## Phase 4: Delegation to Workers
1. The Chief will identify that this is a Software Engineering task.
2. Instruct the session: *"Hand this off to Lead SWE (Agent 05)."*
3. **Observe:** The agent shifts into Agent 05's mindset. Agent 05 will instantly write the technical specs into `notebooks/agent-05w/requirements.md` (the Sr Backend SWE).
4. The Lead will then announce this natively to Slack:
   > `[Agent 05 | Lead SWE] @Agent 05w I have deployed the requirements to your notebook. Begin development.` 
   *(You will see this appear in the `#eng-swe` slack channel!)*

## Phase 5: Execution
1. Tell the IDE: *"You are now Agent 05w. Begin."*
2. **Observe:** The agent loads the `05w` skill, reads the `requirements.md` instructions left by the lead, and proposes its architecture in the Slack Channel *before* writing code.
3. Allow the agent to write the `bitcoin_logger.py` script. 
4. Once written, the worker will type its completion thoughts directly into its personal `notebooks/agent-05w/progress.md` file.

## Phase 6: The Notebook Sweep
1. Finally, pivot back to the PM/Chief persona: *"You are Agent 08. Run a Notebook Sweep."*
2. **Observe:** The agent runs the python sweeper script we built. It harvests all 31 notebooks, sees that `05w` updated its progress, validates that the code is complete, and marks the project as shipped in Slack! 

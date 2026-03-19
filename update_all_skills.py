import os
import re

AGENT_DATA = {
    "08": {"name": "Agent 08 | Chief Orchestrator", "emoji": ":crown:", "channel": "C0ALJGHPYCT"},
    "09": {"name": "Agent 09 | Research Scientist", "emoji": ":microscope:", "channel": "C0ALNS6TR8E"},
    "01": {"name": "Agent 01 | Product Owner", "emoji": ":dart:", "channel": "C0AM3R8GSU9"},
    "02": {"name": "Agent 02 | Project Manager", "emoji": ":clipboard:", "channel": "C0AM3R8GSU9"},
    "03": {"name": "Agent 03 | Tech Lead", "emoji": ":wrench:", "channel": "C0ALJGHPYCT"},
    "04": {"name": "Agent 04 | Lead Data Eng", "emoji": ":bar_chart:", "channel": "C0ALNS6UQCW"},
    "05": {"name": "Agent 05 | Lead SWE", "emoji": ":computer:", "channel": "C0AL9EQKA4F"},
    "06": {"name": "Agent 06 | Lead Ops", "emoji": ":rocket:", "channel": "C0AM3R7RR33"},
    "07d": {"name": "Agent 7d | CISO", "emoji": ":lock:", "channel": "C0AMK6FBA8Y"},
    "10": {"name": "Agent 10 | QA Lead", "emoji": ":white_check_mark:", "channel": "C0ALMFAKKT7"},
    "11": {"name": "Agent 11 | Git Guardian", "emoji": ":shield:", "channel": "C0ALJGHPYCT"},
    "12": {"name": "Agent 12 | Alert Monitor", "emoji": ":rotating_light:", "channel": "C0AL9ER7LUF"},
    "01w": {"name": "Agent 01w | Product Analyst", "emoji": ":mag:", "channel": "C0AM3R8GSU9"},
    "02w": {"name": "Agent 02w | Scrum Master", "emoji": ":calendar:", "channel": "C0AM3R8GSU9"},
    "03w": {"name": "Agent 03w | Solutions Architect", "emoji": ":triangular_ruler:", "channel": "C0AL9EQKA4F"},
    "04w": {"name": "Agent 04w | Senior Data Eng", "emoji": ":database:", "channel": "C0ALNS6UQCW"},
    "04w2": {"name": "Agent 04w2 | Data Quality Eng", "emoji": ":test_tube:", "channel": "C0ALNS6UQCW"},
    "05w": {"name": "Agent 05w | Senior SWE Backend", "emoji": ":gear:", "channel": "C0AL9EQKA4F"},
    "05w2": {"name": "Agent 05w2 | SWE Systems/Rust", "emoji": ":crab:", "channel": "C0AL9EQKA4F"},
    "05w3": {"name": "Agent 05w3 | SWE Frontend", "emoji": ":art:", "channel": "C0AL9EQKA4F"},
    "06w": {"name": "Agent 06w | DevOps Engineer", "emoji": ":whale:", "channel": "C0AM3R7RR33"},
    "06w2": {"name": "Agent 06w2 | MLOps Engineer", "emoji": ":robot_face:", "channel": "C0AM3R7RR33"},
    "06w3": {"name": "Agent 06w3 | GPU/CUDA/MLX Eng", "emoji": ":zap:", "channel": "C0AM3R7RR33"},
    "07a": {"name": "Agent 07a | Security Analysts", "emoji": ":detective:", "channel": "C0AMK6FBA8Y"},
    "07b": {"name": "Agent 07b | Compliance Eng", "emoji": ":scroll:", "channel": "C0AMK6FBA8Y"},
    "07c": {"name": "Agent 07c | Security Tester", "emoji": ":bug:", "channel": "C0AMK6FBA8Y"},
    "07w": {"name": "Agent 07w | Security Automation", "emoji": ":link:", "channel": "C0AMK6FBA8Y"},
    "09w": {"name": "Agent 09w | Research Engineer", "emoji": ":alembic:", "channel": "C0ALNS6TR8E"},
    "10w": {"name": "Agent 10w | QA Engineer", "emoji": ":mag_right:", "channel": "C0ALMFAKKT7"},
    "10w2": {"name": "Agent 10w2 | QA Automation", "emoji": ":arrows_counterclockwise:", "channel": "C0ALMFAKKT7"},
    "00": {"name": "Agent 00 | Org Governance", "emoji": ":scroll:", "channel": "C0ALJGHPYCT"}
}

# --- Dynamic Path Resolution ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SLACK_WORKER_PATH = os.path.join(PROJECT_ROOT, "slack_worker.py")

def get_slack_block(agent_id, data):
    return f"""
## Slack Communication Protocol
You must post updates, handoffs, and questions to your designated Slack channel.
Use the Antigravity slack_worker utility to post messages.

**Your Identity:**
- **Name:** {data['name']}
- **Emoji:** {data['emoji']}
- **Channel ID:** {data['channel']} (Post your main updates here)

**How to send a message:**
To send a message, run the python worker in your Antigravity environment:
```bash
python "{SLACK_WORKER_PATH}" {data['channel']} "{data['name']}" "{data['emoji']}" "Your message here"
```
*Note: Always use this exact method when posting to Slack.*
"""

def update_skill_files():
    base_dir = os.path.join(PROJECT_ROOT, "global-skills")
    count = 0
    for folder in os.listdir(base_dir):
        folder_path = os.path.join(base_dir, folder)
        if not os.path.isdir(folder_path):
            continue
            
        skill_path = os.path.join(folder_path, "SKILL.md")
        if not os.path.exists(skill_path):
            continue
            
        print(f"Checking {folder}...")
        match = re.search(r'([0-9]+[a-z0-9]?)', folder)
        if not match:
            print(f"No agent_id match for {folder}")
            continue
            
        agent_id = match.group(1)
        if agent_id not in AGENT_DATA:
            print(f"Agent ID {agent_id} from {folder} not in AGENT_DATA")
            continue
            
        data = AGENT_DATA[agent_id]
        
        with open(skill_path, "r") as f:
            content = f.read()
            
        # Overwrite logic: If protocol section exists, replace it. Otherwise append.
        new_block = get_slack_block(agent_id, data)
        if "## Slack Communication Protocol" in content:
            # Simple regex to replace the section starting with ## Slack Communication Protocol until end of file
            new_content = re.sub(r'## Slack Communication Protocol.*', new_block.strip() + "\n", content, flags=re.DOTALL)
        else:
            new_content = content.strip() + "\n" + new_block
            
        with open(skill_path, "w") as f:
            f.write(new_content)
            
        print(f"Updated {folder} with OS-Agnostic Slack Identity for Agent {agent_id}")
        count += 1
    
    print(f"Successfully updated {count} SKILL.md files.")

if __name__ == "__main__":
    update_skill_files()

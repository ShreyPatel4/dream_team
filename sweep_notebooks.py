#!/usr/bin/env python3
import os
import glob
from datetime import datetime

# Paths
BASE_DIR = os.path.expanduser("~/.gemini/antigravity")
NOTEBOOKS_DIR = os.path.join(BASE_DIR, "notebooks")
CONTEXT_STORE = os.path.join(BASE_DIR, "context-store")

def read_file(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            content = f.read().strip()
            return content if content else "_No current entries._"
    return "_File not found._"

def sweep_notebooks():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(CONTEXT_STORE, f"chief-{timestamp}-sweep.md")
    
    agent_dirs = sorted(glob.glob(os.path.join(NOTEBOOKS_DIR, "agent-*")))
    
    with open(report_path, "w") as report:
        report.write(f"# 🧹 Automated Notebook Sweep Report\n")
        report.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        has_blockers = False
        blocker_content = ""
        
        progress_content = ""
        
        for adir in agent_dirs:
            agent_id = os.path.basename(adir).replace("agent-", "")
            
            prog = read_file(os.path.join(adir, "progress.md"))
            block = read_file(os.path.join(adir, "blockers.md"))
            ideas = read_file(os.path.join(adir, "ideas.md"))
            
            # Simple check if there's actual content beyond headers or empty indicators
            if block and block != "_No current entries._" and "_No items_" not in block and "No blockers" not in block:
                has_blockers = True
                blocker_content += f"### 🚨 Agent {agent_id} is BLOCKED\n{block}\n\n"
                
            progress_content += f"### Agent {agent_id}\n"
            progress_content += f"**Progress:**\n{prog}\n"
            if ideas and ideas != "_No current entries._":
                progress_content += f"**Ideas/Initiatives:**\n{ideas}\n"
            progress_content += "\n---\n"
            
        if has_blockers:
            report.write("## 🚨 ACTIVE BLOCKERS DETECTED\n")
            report.write("These issues require immediate Lead or PM intervention:\n\n")
            report.write(blocker_content)
            report.write("---\n\n")
        else:
            report.write("## ✅ No Active Blockers\n\n---\n\n")
            
        report.write("## 📝 Progress Updates\n\n")
        report.write(progress_content)

    print(f"Sweep complete! Report generated at: {report_path}")

if __name__ == "__main__":
    sweep_notebooks()

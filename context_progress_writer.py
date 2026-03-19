import os
import datetime
from typing import List, Dict

class ContextProgressWriter:
    """Deterministically formats and writes to the global context_progress.md store."""
    
    def __init__(self, store_path: str):
        self.store_path = store_path
        
    def render_timestamp(self) -> str:
        return datetime.datetime.now().isoformat()
        
    def write_session_end(self, 
                          project_name: str,
                          status: str,
                          agent_id: str,
                          current_state_summary: str,
                          completed_tasks: List[str],
                          in_progress_tasks: List[Dict[str, str]],
                          whats_next: List[str],
                          arch_decisions: List[str],
                          key_files: List[str],
                          sprint_number: int,
                          budget_spent: float,
                          budget_total: float,
                          blockers: str,
                          notes: str):
        
        content = f"""# Project: {project_name}
## Status: {status}
## Last Updated: {self.render_timestamp()}
## Updated By: Agent {agent_id}

---

## Current State
{current_state_summary}

## What Was Just Completed
"""
        if not completed_tasks:
            content += "- None\n"
        for task in completed_tasks:
            content += f"- {task}\n"
            
        content += "\n## What's In Progress\n"
        if not in_progress_tasks:
            content += "- [null]: No active tasks currently assigned in sprint, status: IDLE\n"
        for pt in in_progress_tasks:
            content += f"- [{pt.get('id', 'N/A')}]: {pt.get('desc', 'N/A')} assigned to {pt.get('agent', 'N/A')}, status: {pt.get('status', 'IN_PROGRESS')}\n"
            content += f"  - Approach: {pt.get('approach', 'N/A')}\n"
            content += f"  - Files touched: {pt.get('files', 'N/A')}\n"
            content += f"  - Blockers: {pt.get('blockers', 'none')}\n"
            
        content += "\n## What's Next (Ordered)\n"
        if not whats_next:
            content += "1. None\n"
        for i, task in enumerate(whats_next, 1):
            content += f"{i}. {task}\n"
            
        content += "\n## Architecture Decisions (Append-Only Log)\n"
        if not arch_decisions:
            content += "- None\n"
        for dec in arch_decisions:
            content += f"- {dec}\n"
            
        content += "\n## Key Files\n"
        if not key_files:
            content += "- None\n"
        for kf in key_files:
            content += f"- {kf}\n"
            
        content += f"""
## Sprint State
- Sprint: {sprint_number}
- Started: {datetime.datetime.now().strftime('%Y-%m-%d')}
- Tasks total: {len(completed_tasks) + len(in_progress_tasks)}, Done: {len(completed_tasks)}, In progress: {len(in_progress_tasks)}, Blocked: {1 if blockers and blockers != 'none' else 0}
- Budget spent: ${budget_spent:.2f} of ${budget_total:.2f}
- Burn rate: $0.00/min

## Dependencies & Blockers
- {blockers}

## Notes for Next Session
{notes}
"""

        with open(self.store_path, "w") as f:
            f.write(content)

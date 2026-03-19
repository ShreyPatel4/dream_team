import datetime
from typing import List, Dict

class TemplateEngine:
    """Generates structured standard templates without requiring LLM inference to format."""

    @staticmethod
    def get_date() -> str:
        return datetime.datetime.now().strftime('%Y-%m-%d')

    def render_approach_proposal(self, task_id: str, agent_id: str, role: str, 
                                 task_title: str, task_desc: str, approach: str, 
                                 files: List[str], tests: List[str], effort: str) -> str:
        return f"""# Approach Proposal — {task_id}
## Agent: {agent_id} | {role}
## Task: {task_title}
## Date: {self.get_date()}

## Understanding
{task_desc}

## Proposed Approach
{approach}

## Files I Will Touch
{self._list_to_str(files)}

## Tests I Will Write
{self._list_to_str(tests)}

## Questions / Concerns
[Worker fills this — if empty, auto-approve. If non-empty, lead reviews.]

## Estimated Effort
{effort}
"""

    def render_requirements_handoff(self, task_id: str, worker_id: str, worker_role: str,
                                    lead_id: str, lead_role: str, task_desc: str,
                                    rationale: str, approach: str, files: List[str],
                                    patterns: List[str], tests: List[str], edge_cases: List[str],
                                    budget_tokens: int, budget_cost: float, max_time: str) -> str:
        return f"""# Task Requirements — {task_id}
## For: Agent {worker_id} | {worker_role}
## From: Agent {lead_id} | {lead_role}
## Date: {self.get_date()}

## What You're Building
{task_desc}

## Why
{rationale}

## Approach (Follow This)
{approach}

## Files to Touch
{self._list_to_str(files)}

## Patterns to Follow
{self._list_to_str(patterns)}

## Tests Required
{self._list_to_str(tests)}

## Edge Cases to Handle
{self._list_to_str(edge_cases)}

## When You're Done
1. Run all tests: `pytest tests/`
2. Update your progress.md
3. Commit: `type(scope): description [{task_id}]`
4. Post in dept Slack: "{task_id} complete, ready for review"

## Budget
- Max tokens: {budget_tokens}
- Max cost: ${budget_cost:.2f}
- Max time: {max_time}
"""

    def render_sprint_summary(self, sprint_number: int, project_name: str, start_date: str, end_date: str,
                              tasks_completed: List[Dict[str, str]], qa_submissions: int,
                              qa_first_pass: int, qa_reworks: int, budget_allocated: float,
                              budget_spent: float, agent_breakdown: str, model_breakdown: str,
                              blockers: List[str], context_notes: str) -> str:
        
        qa_rate = f"{(qa_first_pass / qa_submissions * 100):.1f}%" if qa_submissions > 0 else "N/A"
        
        rows = ""
        for t in tasks_completed:
            rows += f"| {t.get('task')} | {t.get('agent')} | {t.get('started')} | {t.get('completed')} | ${t.get('cost')} | {t.get('tokens')} |\n"

        return f"""# Sprint {sprint_number} Summary — {project_name}
## Generated: {self.get_date()}
## Duration: {start_date} to {end_date}

## Tasks Completed
| Task | Agent | Started | Completed | Cost | Tokens |
|------|-------|---------|-----------|------|--------|
{rows}
## QA Results
- Total submissions: {qa_submissions}
- First-pass rate: {qa_rate}
- Rework cycles: {qa_reworks}

## Budget
- Allocated: ${budget_allocated:.2f}
- Spent: ${budget_spent:.2f}
- By agent: {agent_breakdown}
- By model: {model_breakdown}

## Blockers Encountered
{self._list_to_str(blockers)}

## Context for Next Sprint
{context_notes}
"""

    def render_trello_card(self, ticket_id: str, dept: str, number: int, 
                           title: str, priority: str, color: str, lead_id: str, 
                           desc: str, acceptance: List[str], deps: List[str]) -> str:
        
        acc_str = "\n".join([f"- [ ] {a}" for a in acceptance])
        
        return f"""Title: {ticket_id}-{dept}-{number}: {title}
Labels: {priority}, {color}
Members: {lead_id}
Description: |
  ## Task Specification
  {desc}
  
  ## Acceptance Criteria
  {self._list_to_str(acceptance)}
  
  ## Context
  See: context_progress.md
  
  ## Dependencies
  {self._list_to_str(deps)}
Checklist:
{acc_str}
"""

    def _list_to_str(self, items: List[str]) -> str:
        if not items:
            return "- None"
        return "\n".join([f"- {item}" for item in items])

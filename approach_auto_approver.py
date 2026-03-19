from typing import List, Optional

class TaskRequirements:
    def __init__(self, task_id: str, effort: str):
        self.task_id = task_id
        self.effort = effort

class ApproachProposal:
    def __init__(self, task_id: str, agent_id: str, questions_or_concerns: List[str] = None):
        self.task_id = task_id
        self.agent_id = agent_id
        self.questions_or_concerns = questions_or_concerns or []

class ApprovalDecision:
    def __init__(self, approved: bool, method: str, reason: str):
        self.approved = approved
        self.method = method
        self.reason = reason

class ApproachAutoApprover:
    """Zero API calls when a worker understands instructions and raises no concerns."""

    def check(self, proposal: ApproachProposal, reqs: TaskRequirements) -> ApprovalDecision:
        if not proposal.questions_or_concerns:
            return ApprovalDecision(
                approved=True, 
                method="auto",
                reason="Worker confirmed understanding, no concerns raised."
            )

        return ApprovalDecision(
            approved=False, 
            method="needs_lead_review",
            reason=f"Worker raised {len(proposal.questions_or_concerns)} concerns."
        )

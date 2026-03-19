from typing import List

class LeadAssessment:
    def __init__(self, agent_id: str, agree: bool, refinements: List[str], effort: str, can_self_handle: bool, needs_workers: List[str], approach: str):
        self.agent_id = agent_id
        self.agree = agree
        self.refinements = refinements
        self.effort = effort
        self.can_self_handle = can_self_handle
        self.needs_workers = needs_workers
        self.approach = approach

class ConsensusResult:
    def __init__(self, reached: bool, action: str, merged_plan: List[str] = None, dissenters: List[LeadAssessment] = None):
        self.reached = reached
        self.action = action
        self.merged_plan = merged_plan or []
        self.dissenters = dissenters or []

class ConsensusChecker:
    """Deterministic checking of lead assessments to skip LLM mediation when possible."""

    def check(self, assessments: List[LeadAssessment]) -> ConsensusResult:
        if not assessments:
            return ConsensusResult(reached=True, action="PROCEED")

        all_agree = all(a.agree for a in assessments)
        has_refinements = any(a.refinements for a in assessments)

        if all_agree and not has_refinements:
            return ConsensusResult(reached=True, action="PROCEED")

        if all_agree and has_refinements:
            merged = [r for a in assessments for r in a.refinements]
            return ConsensusResult(reached=True, action="PROCEED_WITH_REFINEMENTS", merged_plan=merged)

        dissenters = [a for a in assessments if not a.agree]
        return ConsensusResult(reached=False, action="CHIEF_DECIDES", dissenters=dissenters)

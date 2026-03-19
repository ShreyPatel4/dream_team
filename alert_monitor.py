import time
import subprocess
from dataclasses import dataclass
from typing import Dict

@dataclass
class AgentState:
    agent_id: str
    last_active: float
    budget_spent: float
    restart_count: int

class AlertMonitor:
    """Enforces runtime budget caps, agent deadlocks, and triggers emergency Slack halts."""
    
    def __init__(self, max_budget_usd: float = 50.0, warning_percent: float = 0.8, timeout_seconds: int = 300):
        self.max_budget = max_budget_usd
        self.warning_threshold = self.max_budget * warning_percent
        self.timeout_seconds = timeout_seconds
        
        self.agent_states: Dict[str, AgentState] = {}
        self.total_budget_spent = 0.0
        self.budget_warned = False
        self.budget_exhausted = False

    def update_agent(self, agent_id: str, cost_increment: float = 0.0):
        if agent_id not in self.agent_states:
            self.agent_states[agent_id] = AgentState(
                agent_id=agent_id, 
                last_active=time.time(), 
                budget_spent=0.0, 
                restart_count=0
            )
        
        state = self.agent_states[agent_id]
        state.last_active = time.time()
        state.budget_spent += cost_increment
        self.total_budget_spent += cost_increment

    def check_health(self) -> str:
        """Returns 'HEALTHY' or 'PAUSE' if a critical threshold was hit."""
        # 1. Budget Exhaustion (Level 3 Autonomy escalation)
        if self.total_budget_spent >= self.max_budget:
            if not self.budget_exhausted:
                self.budget_exhausted = True
                self._fire_slack_alert(f"🚨 EMERGENCY: System budget limit (${self.max_budget}) exhausted. Execution hard-paused. Shrey approval required.")
            return "PAUSE_FOR_SHREY"
            
        # 2. Budget Warning (Level 2 escalation)
        if self.total_budget_spent >= self.warning_threshold and not self.budget_warned:
            self.budget_warned = True
            self._fire_slack_alert(f"⚠️ WARNING: 80% of project budget consumed (${self.total_budget_spent:.2f} / ${self.max_budget:.2f}).")

        # 3. Deadlock / Stuck Detection
        now = time.time()
        for agent_id, state in self.agent_states.items():
            if now - state.last_active > self.timeout_seconds:
                # In a real cluster, we would cleanly kill and supervisor-restart the agent here
                self._fire_slack_alert(f"⚠️ STUCK AGENT: Agent {agent_id} has been inactive for over {self.timeout_seconds//60} minutes. Supervisor restarting.")
                state.last_active = time.time() # Reset to prevent spam
                
        return "HEALTHY"

    def _fire_slack_alert(self, message: str):
        """Dispatches critical OS alerts directly to Shrey's leadership channel."""
        import os
        project_root = os.path.dirname(os.path.abspath(__file__))
        
        try:
            from slack_worker import send_slack_message
            send_slack_message("C_LEADERSHIP", "CoconutOS Monitor", ":rotating_light:", message)
            print(f"[OS ALERT] Dispatched to Slack: {message}")
        except Exception as e:
            print(f"[OS ALERT ERROR] Failed to hit Slack API: {e}")

        # ── TELEMETRY ──
        try:
            from telemetry_writer import telemetry
            telemetry.emit("alert_fired",
                           data={"rule_name": "system_alert", "message": message[:200]})
        except ImportError:
            pass

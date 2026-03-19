import os
import glob
import time
import subprocess
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types
import anthropic
from prometheus_client import start_http_server, Counter, Gauge
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from llm_gateway import LLMGateway
from alert_monitor import AlertMonitor

try:
    from telemetry_writer import telemetry as _tel
except ImportError:
    class _Noop:
        def emit(self, *a, **kw): pass
    _tel = _Noop()

_current_project_id = None  # Set when processing a trigger

# --- OpenTelemetry Jaeger Setup ---
resource = Resource(attributes={"service.name": "dreamteam-orchestrator"})
provider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True))
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

# --- Observability Metrics (Phase 7) ---
LLM_CALLS = Counter('dreamteam_llm_calls_total', 'Total LLM API calls', ['agent_id', 'model'])
TASKS_COMPLETED = Counter('dreamteam_tasks_completed_total', 'Total tasks completed', ['agent_id'])
BUDGET_SPENT = Gauge('dreamteam_budget_spent_usd', 'Total budget spent in USD')

# --- Dynamic Cross-Platform Path Resolution ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
CLAUDE_API = os.environ.get("CLAUDE_API")

# The Antigravity IDE explicitly lives in the user's home directory across all OS
BASE_DIR = os.path.join(os.path.expanduser("~"), ".gemini", "antigravity")
INBOX_DIR = os.path.join(BASE_DIR, "context-store", "inbox")
SKILLS_DIR = os.path.join(BASE_DIR, "skills")
NOTEBOOKS_DIR = os.path.join(BASE_DIR, "notebooks")
CONFIG_PATH = os.path.join(PROJECT_ROOT, "coconutos.yml")

gateway = LLMGateway(CONFIG_PATH, GEMINI_API_KEY, CLAUDE_API)
monitor = AlertMonitor(max_budget_usd=50.0, warning_percent=0.8, timeout_seconds=300)

def get_agent_skill(agent_selector):
    """Finds the SKILL.md for a given agent by fuzzy matching the directory name."""
    agent_dirs = glob.glob(os.path.join(SKILLS_DIR, f"*{agent_selector}*"))
    if not agent_dirs:
        return None
    
    skill_path = os.path.join(agent_dirs[0], "SKILL.md")
    if os.path.exists(skill_path):
        with open(skill_path, "r") as f:
            return f.read()
    return None

def execute_bash_tool(command):
    """Executes a bash command and returns the output."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.stderr:
            print(f"   [Tool Stderr]: {result.stderr.strip()}")
        if result.stdout:
            print(f"   [Tool Stdout]: {result.stdout.strip()}")
        return result.stdout.strip()
    except Exception as e:
        print(f"   [Tool Exception]: {e}")
        return f"Error executing command: {e}"

def write_to_notebook(agent_id, file_name, content):
    """Appends to a specific agent's notebook file."""
    notebook_path = os.path.join(NOTEBOOKS_DIR, f"agent-{agent_id}", file_name)
    os.makedirs(os.path.dirname(notebook_path), exist_ok=True)
    with open(notebook_path, "a") as f:
        f.write(content + "\n\n")

def run_agent_turn(agent_selector, prompt_context):
    """Spins up an LLM thread for a specific agent and executes its decisions."""
    with tracer.start_as_current_span(f"agent_turn_{agent_selector}") as span:
        span.set_attribute("agent.id", agent_selector)
        print(f"\n[{agent_selector}] Booting Persona...")
        
        skill_content = get_agent_skill(agent_selector)
        if not skill_content:
            print(f"Error: Could not find skill definition for agent {agent_selector}")
            return None

    # We strongly instruct the LLM to use explicit keywords so we can parse its Bash/Handoff decisions
    system_instruction = f"""
    You are part of an autonomous AGI loop. 
    You must strictly follow the rules defined in your SKILL.md file below.
    
    ## YOUR IDENTITY DEFINITION
    {skill_content}
    
    ## AUTOMATION INSTRUCTIONS
    As an AGI agent, you do not have fingers. I am a Python script wrapping your brain.
    If you need to use the `slack-bridge.sh` or `trello-tool.sh` OR run any system command, you must output the EXACT command 
    wrapped in ```bash blocks. I will execute it for you.
    
    CRITICAL BASH RULE: You MUST wrap ALL file paths containing spaces in double quotes! 
    Example BAD: ls ~/{os.path.basename(PROJECT_ROOT)}/Data-Kitchen
    Example GOOD: ls "{os.path.join(PROJECT_ROOT, 'Data-Kitchen')}"
    
    If you need to write to another agent's notebook, or your own, use this format exactly:
    [WRITE_NOTEBOOK: agent_id, filename]
    Your content here
    [/WRITE_NOTEBOOK]
    
    If you are ready to hand off execution to another agent, end your response with:
    [HANDOFF: agent_id]
    
    IMPORTANT: You must always conclude your turn by either handing off to another agent, OR using the slack-bridge.sh to ask the user a question or provide an update. Never execute commands and just stay completely silent.
    """

    print(f"[{agent_selector}] Analyzing context...")
    
    try:
        output, model_used = gateway.generate(agent_selector, system_instruction, prompt_context,
                                              project_id=_current_project_id)
        LLM_CALLS.labels(agent_id=agent_selector, model=model_used).inc()
        cost = 0.01
        BUDGET_SPENT.inc(cost) 
        monitor.update_agent(agent_selector, cost)
    except Exception as e:
        _tel.emit("llm_call_failed", _current_project_id, agent_selector,
                  data={"error": str(e)})
        print(f"[{agent_selector}] Inference Error: {e}")
        return None

    print(f"[{agent_selector}] Decision made. Executing tools...")

    # Parse and execute Bash requests
    bash_commands = re.findall(r'```bash\n(.*?)\n```', output, re.DOTALL)
    for cmd in bash_commands:
        # Fix unquoted macOS paths with spaces
        raw_path = PROJECT_ROOT
        quoted_path = f'"{raw_path}"'
        if raw_path in cmd and quoted_path not in cmd:
            cmd = cmd.replace(raw_path, quoted_path)
            
        print(f"-> Executing: {cmd}")
        execute_bash_tool(cmd)

    # Parse and execute Notebook writes
    notebook_writes = re.findall(r'\[WRITE_NOTEBOOK:\s*([^,]+),\s*([^\]]+)\]\n(.*?)\[\/WRITE_NOTEBOOK\]', output, re.DOTALL)
    for agent_id, filename, content in notebook_writes:
        agent_id = agent_id.strip()
        filename = filename.strip()
        print(f"-> Writing to {agent_id}/{filename}")
        write_to_notebook(agent_id, filename, content.strip())

        handoff_match = re.search(r'\[HANDOFF:\s*([^\]]+)\]', output)
        if handoff_match:
            next_agent = handoff_match.group(1).strip()
            span.set_attribute("agent.handoff", next_agent)
            TASKS_COMPLETED.labels(agent_id=agent_selector).inc()
            print(f"[{agent_selector}] Task completed. Handing off to {next_agent}...")
            return next_agent
            
        print(f"[{agent_selector}] Execution paused. Waiting for next event.")
        return None

def main_loop():
    print("Prometheus metrics server starting on port 8000...")
    start_http_server(8000)
    
    print("AGI Orchestrator booted. Watching context-store/inbox for Slack Triggers...")
    
    if not GEMINI_API_KEY or not CLAUDE_API:
        print("ERROR: API keys missing from .env file. The Multi-Provider Brain needs GEMINI_API_KEY and CLAUDE_API.")
        return

    while True:
        # 0. System Health Checks (Budget caps, stuck agents)
        if monitor.check_health() == "PAUSE_FOR_SHREY":
            print("🚨 SYSTEM PAUSED: Budget limit reached or critical error. Sleeping 60s.")
            time.sleep(60)
            continue
            
        # 1. Sweep Inbox
        inbox_files = glob.glob(os.path.join(INBOX_DIR, "*.md"))
        
        for file in inbox_files:
            print(f"\n🚨 [TRIGGER DETECTED] Processing {os.path.basename(file)}")
            
            with open(file, "r") as f:
                context = f.read()
                
            # Deterministic Request Classification (Phase 6)
            try:
                from request_classifier import RequestClassifier, IncomingRequest, load_project_context
                classifier = RequestClassifier()
                proj_context = load_project_context(os.path.join(BASE_DIR, "context-store", "active_projects.json"))
                req = IncomingRequest(raw_content=context, source="slack")
                req_type = classifier.classify(req, proj_context)
                print(f"   -> [Deterministic Router]: Classified request as {req_type.value}")
                classification_str = req_type.value
            except Exception as e:
                print(f"   -> [Router Error]: Defaults to NEW_PROJECT. {e}")
                classification_str = "NEW_PROJECT"
                
            # Delete the trigger so we don't process it twice
            os.remove(file)
            
            # 2. Begin Recursion Loop starting with the Chief
            current_agent = "08"
            _tel.emit("agent_status_change", _current_project_id, "08",
                      data={"from_status": "IDLE", "to_status": "PLANNING",
                            "reason": "inbox_trigger"})
            active_context = f"NEW SLACK REQUEST TRIGGERED (Classification: {classification_str}):\n\n{context}"
            
            # The AGI Loop: Keep handing off until an agent doesn't specify a successor
            while current_agent:
                _tel.emit("agent_spawned", _current_project_id, current_agent,
                          data={"role": current_agent, "spawn_reason": "handoff"})
                next_agent = run_agent_turn(current_agent, active_context)
                if next_agent != current_agent:
                    _tel.emit("agent_killed", _current_project_id, current_agent,
                              data={"reason": "handoff_complete"})
                current_agent = next_agent
                active_context = "Your lead has handed off a task to you. Read your notebook requirements.md file and execute your SKILL.md protocol."
                
        time.sleep(5)

if __name__ == "__main__":
    main_loop()

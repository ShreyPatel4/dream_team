import os
import json
import time
import ssl
import logging
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)
import certifi

# Fix for macOS Python SSL Certificate Error in Websocket Clients
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["SSL_CERT_DIR"] = certifi.where()
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv

# --- Dynamic Cross-Platform Path Resolution ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# Ensure these are loaded in your environment from the .env file
# or use python-dotenv here if installed
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")
ALLOWED_WORKSPACE_ID = "T0AL981MNP9"  # Coconut Labs

# The Antigravity IDE explicitly lives in the user's home directory across all OS
BASE_DIR = os.path.join(os.path.expanduser("~"), ".gemini", "antigravity")
INBOX_DIR = os.path.join(BASE_DIR, "context-store", "inbox")

# Initialize the Slack App
app = App(token=SLACK_BOT_TOKEN)

def display_os_notification(title, message):
    """Fires a generic log. Replaces macOS-only osascript for OS Agnostic support."""
    print(f"\n[SYSTEM NOTIFICATION] {title}: {message}\n")

@app.middleware
def log_request(logger, body, next):
    logger.debug(f"RAW SLACK SOCKET PAYLOAD RECEIVED: {list(body.keys())}")
    return next()

@app.event("app_mention")
def handle_app_mention_events(body, logger):
    try:
        team_id = body.get("team_id")
        
        # 🚨 SECURITY GUARDRAIL 🚨
        # Strictly ignore any mentions coming from unauthorized workspaces
        if team_id != ALLOWED_WORKSPACE_ID:
            logger.warning(f"BLOCKED: Received event from unauthorized Workspace ID: {team_id}")
            return
            
        event = body.get("event", {})
        user = event.get("user")
        text = event.get("text")
        channel = event.get("channel")
        
        logger.info(f"Authorized mention received in channel {channel} from user {user}")
        
        # Ensure inbox directory exists
        os.makedirs(INBOX_DIR, exist_ok=True)
        
        # Persist the request tracking explicitly in the Context Store Inbox
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{INBOX_DIR}/slack_trigger_{timestamp}.md"
        
        with open(filename, "w") as f:
            f.write(f"## Slack Request via Auto-Spawn\n")
            f.write(f"- **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- **Channel:** {channel}\n")
            f.write(f"- **User:** <@{user}>\n\n")
            f.write(f"### Raw Message\n")
            f.write(f"{text}\n")
            
        # Fire system notification alerting user that the org needs attention
        display_os_notification(
            "Agent 08 Summoned via Slack! 🚨", 
            "The Dream Team just received a new Slack request."
        )

        # ── TELEMETRY ──
        try:
            from telemetry_writer import telemetry
            telemetry.emit("slack_message_received",
                           data={"channel_id": channel, "sender": user,
                                 "message_preview": text[:100] if text else "",
                                 "is_mention": True})
        except ImportError:
            pass
        
    except Exception as e:
        logger.error(f"Error handling event: {e}")

if __name__ == "__main__":
    if not SLACK_BOT_TOKEN or not SLACK_APP_TOKEN:
        print("Error: Required Slack Tokens not found. Please ensure they are loaded into the environment.")
        exit(1)
        
    print(f"Starting Dream Team Slack Listener with restriction to Workspace: {ALLOWED_WORKSPACE_ID}...")
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()

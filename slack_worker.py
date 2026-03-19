import sys
import os
import requests
import json
from dotenv import load_dotenv

def send_slack_message(channel_id, agent_name, emoji, message):
    # Dynamic path resolution to find .env in project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(os.path.join(project_root, ".env"))
    
    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        print("Error: SLACK_BOT_TOKEN not found in environment.")
        sys.exit(1)
        
    payload = {
        "channel": channel_id,
        "text": message,
        "username": agent_name,
        "icon_emoji": emoji
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    response = requests.post("https://slack.com/api/chat.postMessage", headers=headers, json=payload)
    
    if response.status_code == 200 and response.json().get("ok"):
        print(f"Message sent successfully to channel {channel_id} as {agent_name}")
        try:
            from telemetry_writer import telemetry
            telemetry.emit("slack_message_sent",
                           project_id=os.environ.get("CURRENT_PROJECT"),
                           agent_id=agent_name[:4].replace(" ", ""),
                           data={"channel_id": channel_id, "agent_identity": agent_name,
                                 "message_preview": message[:100]})
        except ImportError:
            pass
    else:
        print(f"Failed to send message: {response.text}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python slack_worker.py <channel_id> <agent_name> <emoji> <message>")
        sys.exit(1)
        
    send_slack_message(sys.argv[1], sys.argv[2], sys.argv[3], " ".join(sys.argv[4:]))

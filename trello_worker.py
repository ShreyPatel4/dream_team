import sys
import os
import requests
from dotenv import load_dotenv

try:
    from telemetry_writer import telemetry as _tel
except ImportError:
    class _Noop:
        def emit(self, *a, **kw): pass
    _tel = _Noop()

def trello_tool(command, *args):
    project_root = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(os.path.join(project_root, ".env"))
    
    api_key = os.environ.get("TRELLO_API_KEY")
    token = os.environ.get("TRELLO_TOKEN")
    
    if not api_key or not token:
        print("Error: TRELLO_API_KEY and TRELLO_TOKEN must be set.")
        sys.exit(1)
        
    auth = {"key": api_key, "token": token}
    
    if command == "create_card":
        if len(args) < 3:
            print("Usage: trello_worker.py create_card <list_id> <title> <description>")
            sys.exit(1)
        list_id, title, desc = args[0], args[1], args[2]
        url = "https://api.trello.com/1/cards"
        params = {**auth, "idList": list_id}
        data = {"name": title, "desc": desc}
        response = requests.post(url, params=params, json=data)
        print(response.text)
        _tel.emit("trello_card_created",
                  project_id=os.environ.get("CURRENT_PROJECT"),
                  agent_id="02",
                  data={"title": title, "list_id": list_id})
        
    elif command == "move_card":
        if len(args) < 2:
            print("Usage: trello_worker.py move_card <card_id> <new_list_id>")
            sys.exit(1)
        card_id, list_id = args[0], args[1]
        url = f"https://api.trello.com/1/cards/{card_id}"
        params = {**auth, "idList": list_id}
        response = requests.put(url, params=params)
        print(response.text)
        _tel.emit("trello_card_moved",
                  project_id=os.environ.get("CURRENT_PROJECT"),
                  agent_id="02",
                  data={"card_id": card_id, "to_list": list_id})
        
    elif command == "add_comment":
        if len(args) < 2:
            print("Usage: trello_worker.py add_comment <card_id> <text>")
            sys.exit(1)
        card_id, text = args[0], args[1]
        url = f"https://api.trello.com/1/cards/{card_id}/actions/comments"
        params = {**auth}
        data = {"text": text}
        response = requests.post(url, params=params, json=data)
        print(response.text)
        _tel.emit("trello_comment_added",
                  project_id=os.environ.get("CURRENT_PROJECT"),
                  agent_id="02",
                  data={"card_id": card_id, "text_preview": text[:80]})
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python trello_worker.py <command> <args...>")
        sys.exit(1)
    trello_tool(sys.argv[1], *sys.argv[2:])

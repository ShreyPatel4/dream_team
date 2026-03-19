# MCP Configuration for Antigravity

## Overview
These MCP servers enable agents to communicate via Slack, manage tasks in Trello,
send formal deliverables via Gmail, and schedule meetings via Calendar.

## Antigravity MCP Setup

Add to your Antigravity settings (Settings → MCP Servers):

```json
{
  "mcpServers": {
    "slack": {
      "type": "url",
      "url": "https://mcp.slack.com/sse",
      "name": "slack-mcp",
      "description": "Slack workspace for agent communication"
    },
    "gmail": {
      "type": "url", 
      "url": "https://gmail.mcp.claude.com/mcp",
      "name": "gmail-mcp",
      "description": "Gmail for formal deliverables"
    },
    "google-calendar": {
      "type": "url",
      "url": "https://gcal.mcp.claude.com/mcp",
      "name": "gcal-mcp",
      "description": "Calendar for sprint ceremonies"
    }
  }
}
```

## Trello Options

### Option A: Slack-Trello Power-Up (Recommended to start)
1. Add Trello Power-Up to your Slack workspace
2. Link your Trello board
3. PM uses Slack commands: `/trello add [card]`, `/trello move [card] [list]`
4. Cards created in Slack auto-link to Trello

### Option B: Custom Trello MCP Server
Build a lightweight MCP server wrapping Trello REST API:
```
Endpoints needed:
  - create_card(list, title, description, labels, members)
  - move_card(card_id, target_list)
  - add_comment(card_id, text)
  - list_cards(board_id, list_name)
  - update_card(card_id, fields)
```
This can be a simple FastAPI + MCP wrapper. Agent 6w (DevOps) can build it.

### Option C: Filesystem Fallback
If MCP isn't available, the `project-tracker/kanban.md` file serves as
the fallback. PM maintains it manually. Less ideal but functional.

## Security Notes
- MCP connections use OAuth — no API keys in code
- All MCP traffic is TLS encrypted
- Agent permissions controlled by Slack workspace roles
- Gmail sends require lead review before sending (per constitution)
- No MCP server has write access to production systems

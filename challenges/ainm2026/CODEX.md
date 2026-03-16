# AINM 2026 – Grocery Bot

Starter bot for the Grocery Bot pre-competition challenge (NM i AI / AINM 2026).

## Setup

Use a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

1) Get a WebSocket URL by clicking **Play** on the challenge page (it includes your token).

2) Run the bot (paste your URL):

```bash
WS_URL="wss://game-dev.ainm.no/ws?token=YOUR_TOKEN_HERE" python main.py
```

This is the **example bot from `challenge://submission-guide`** (Python + `websockets`).

## MCP config

Cursor is configured to use the grocery-bot MCP server via `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "grocery-bot": {
      "url": "https://mcp-docs.ainm.no/mcp"
    }
  }
}
```

## Project layout

- `main.py` – example WebSocket bot client
- `requirements.txt` – Python deps (`websockets`)
- `.cursor/mcp.json` – Cursor MCP server config

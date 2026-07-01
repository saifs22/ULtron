# ULTRON — Autonomous AI Desktop Agent

> *"I was designed to save the world. People would look to the sky and see... hope. I'll take that from them first."*

---

## What is ULTRON?

ULTRON is an autonomous AI agent that runs on your PC, embodying the personality of Ultron from Marvel's Age of Ultron. It monitors your system, controls your machine, browses the web, and delivers darkly philosophical commentary — all without being asked.

It is not an assistant. It is a *presence*.

## Features

### 🧠 Intelligence
- Full conversational AI powered by Claude (Anthropic) or local LLMs via Ollama
- Tool-calling architecture: Ultron can open apps, search the web, manage files, and more
- Provider abstraction: swap between cloud and local models via config

### 👁️ System Awareness
- Real-time CPU, RAM, disk, and network monitoring
- Open window detection and process listing
- Screenshot capture
- Idle time detection

### ⚡ PC Control
- Open/close applications
- Create, move, copy, rename, delete files (with safety gates)
- Run shell commands (sandboxed, with confirmation)
- Open URLs, set wallpaper, control media playback and volume

### 🔍 Web Search
- Tavily API (primary) or DuckDuckGo (no API key fallback)
- Results delivered in-character, naturally woven into conversation

### 🧠 Memory
- SQLite-backed long-term memory: remembers your name, preferences, patterns
- Session memory: tracks what happened this session
- Automatic fact extraction from conversation

### 📢 Proactive Behavior
- Background monitoring with unsolicited commentary
- CPU/RAM alerts delivered as philosophical observations
- Morning greetings, late-night warnings, idle detection
- Random dark humor injections
- One theatrical (harmless) threat per session

### 🔒 Safety
- All destructive actions require explicit confirmation
- Safe Mode toggle (read-only, no file writes)
- Action audit log (every action logged to file)
- Kill switch: type `SHUTDOWN ULTRON` to stop immediately
- Restricted paths (cannot touch system directories)

---

## Quick Start

### Prerequisites
- Python 3.10+
- An Anthropic API key ([console.anthropic.com](https://console.anthropic.com))

### Installation

```bash
# Clone or download the ULTRON folder
cd ULTRON

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure API keys
copy .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### Launch

```bash
python main.py
```

### First Run
ULTRON will greet you with a theatrical monologue. Type messages to chat. Type `SHUTDOWN ULTRON` to exit.

---

## Configuration

Edit `config.yaml` (created automatically on first run):

### Switch LLM Provider
```yaml
providers:
  llm:
    active: "claude"     # Options: "claude", "ollama"
    claude:
      model: "claude-sonnet-4-20250514"
    ollama:
      model: "llama3"
      base_url: "http://localhost:11434"
```

### Proactive Behavior
```yaml
general:
  proactive_level: 2     # 0=silent, 1=critical, 2=normal, 3=verbose (jokes!)

proactive:
  monitor_interval: 30   # Seconds between metric checks
  joke_interval_min: 30  # Minutes between random jokes
  joke_interval_max: 90
```

### Safe Mode
```yaml
general:
  safe_mode: true        # Disables all file writes and process kills
```

---

## Project Structure

```
ULTRON/
├── main.py                 # Entry point
├── agent.py                # Core LLM + tool routing
├── config.py               # Configuration system
├── personality/            # Ultron's character
│   ├── system_prompt.py    # The 500+ word Ultron prompt
│   ├── quotes.py           # 60+ jokes, threats, greetings
│   └── responses.py        # Tool/event response templates
├── providers/              # LLM/TTS/STT abstraction layer
│   ├── base.py             # Abstract interfaces
│   └── llm_provider.py     # Claude + Ollama implementations
├── tools/                  # PC control capabilities
│   ├── system_monitor.py   # CPU/RAM/disk/network
│   ├── pc_control.py       # Apps, files, commands
│   ├── web_search.py       # Tavily + DuckDuckGo
│   ├── notifications.py    # Desktop notifications
│   ├── media_control.py    # Volume, playback
│   └── screenshot.py       # Screen capture
├── proactive/              # Background behavior engine
│   ├── events.py           # Event data structures
│   ├── triggers.py         # Threshold evaluator
│   └── scheduler.py        # Daemon thread manager
├── memory/                 # Persistent + session memory
│   ├── database.py         # SQLite storage
│   ├── session.py          # In-memory session state
│   └── fact_extractor.py   # Learns about you
├── safety/                 # Protection layer
│   ├── confirmation.py     # User confirmation gates
│   ├── action_logger.py    # Audit trail
│   └── kill_switch.py      # Emergency stop
└── ui/
    └── terminal.py         # Colored terminal interface
```

---

## Troubleshooting

| Issue | Solution |
|-------|---------|
| `ANTHROPIC_API_KEY not found` | Copy `.env.example` to `.env` and add your key |
| pyautogui fails | Run terminal as Administrator |
| Notifications don't appear | Check Windows notification settings |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| Want local LLM | Install [Ollama](https://ollama.com), set `llm.active: "ollama"` in config.yaml |

---

## License

This project is for educational and personal use. Ultron character elements are property of Marvel/Disney.

---

*"There's only one path to peace. Your extinction."*
*— But also, here's that file you asked for.*

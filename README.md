

# Wayland MCP Server

[![Status: WIP](https://img.shields.io/badge/status-WIP-yellow)](https://github.com/someaka/wayland-mcp)
[![License: GPT3](https://img.shields.io/badge/license-GPT3-blue)](#license)

> **Note:** This package was created because existing screenshot solutions didn't work reliably on my Wayland setup.
> **Wayland MCP** provides screenshot, analysis, mouse and keyboard control tools for modern Linux desktops.

---

## Features
  
  - **Custom VLM integration for analysis**
  - **Images comparison**
  - **Mouse & keyboard input simulation**


## ⚠️ Security Warning

> **WARNING:** Enabling input control gives the MCP server full access to your mouse and keyboard.
> Only use with trusted MCP servers and models.

## Input Control Setup

To enable mouse and keyboard control (move, click, drag, scroll, type):

```bash
./wayland_mcp/setup.sh
```

This configures permissions for `evemu-event` to control input devices.

---

## MCP Server Configuration

Add to your MCP server config (e.g., `.roo/mcp.json`):

```json
{
  "mcpServers": {
    "wayland-screenshot": {
      "command": "uvx",
      "args": ["wayland-mcp"],
      "env": {
        "OPENROUTER_API_KEY": "your-api-key",
        "VLM_MODEL": "qwen/qwen2.5-vl-72b-instruct:free",
        "XDG_RUNTIME_DIR": "/run/user/1000",
        "WAYLAND_MCP_PORT": "4999",
        "PYTHONPATH": "wayland-mcp",
        "DISPLAY": ":0",
        "WAYLAND_DISPLAY": "wayland-0",
        "XDG_SESSION_TYPE": "wayland"
      }
    }
  }
}
```
---

## Development

```bash
git clone https://github.com/someaka/wayland-mcp
cd wayland-mcp
pip install -e .
```

---

## License

GPT3


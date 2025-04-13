# Wayland MCP Server

[![Status: WIP](https://img.shields.io/badge/status-WIP-yellow)](https://github.com/someaka/wayland-mcp)
[![License: GPT3](https://img.shields.io/badge/license-GPT3-blue)](#license)

> **Note:** This package was created because existing screenshot solutions didn't work reliably on my Wayland setup.  
> **Wayland MCP** provides advanced screenshot, analysis, and mouse control tools for modern Linux desktops.

---

## Table of Contents

- [Features](#features)
- [Input Control Setup](#input-control-setup)
  - [Enabling Mouse Functionality](#enabling-mouse-functionality)
  - [MCP Server Environment Configuration](#mcp-server-environment-configuration)
- [Development](#development)
- [License](#license)

---

## Features

- **Custom VLM integration for analysis**
- **Advanced input simulation:**
  - [x] Typing, key presses, clicks
  - [x] Mouse dragging between coordinates
  - [ ] Vertical/horizontal scrolling
  - [ ] Cross-platform support
- **Screen Capture and VLM Integration:** AI-powered screenshot analysis
- **MCP Tools:**
  - `capture_screenshot`: Fullscreen/region capture
  - `analyze_screenshot`: AI analysis of screenshots
  - `capture_and_analyze`: Combined capture+analysis
  - `compare_images`: Visual diff tool

---

## Input Control Setup

### ⚡ Enabling Mouse Functionality

To enable mouse control features (move, click, drag, scroll), **run the setup script**:

```bash
./wayland_mcp/setup.sh
```

This script will configure the necessary permissions for `evemu-event`, allowing the MCP server to control the mouse.

---

### 🛠️ MCP Server Environment Configuration

Add the following to the `"env"` section for your MCP server (e.g., `.roo/mcp.json`):

```json
{
  "mcpServers": {
    "wayland-screenshot": {
      "command": "uvx",
      "args": [
        "wayland-mcp"
      ],
      "env": {
        "OPENROUTER_API_KEY": "your-api-key",
        "VLM_MODEL": "qwen/qwen2.5-vl-72b-instruct:free",
        "XDG_RUNTIME_DIR": "/run/user/1000",
        "WAYLAND_MCP_PORT": "4999",
        "PYTHONPATH": "wayland_mcp",
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
git clone https://github.com/your-repo/wayland-mcp
cd wayland-mcp
pip install -e .
```

---

## License

GPT3

---

*Need help?*  
Open an issue on [GitHub](https://github.com/someaka/wayland-mcp/issues) or check the project discussions for support.



# 🚀 Wayland MCP Server

[![Status: WIP](https://img.shields.io/badge/status-WIP-yellow)](https://github.com/someaka/wayland-mcp)
[![License: GPL3](https://img.shields.io/badge/license-GPL3-blue)](#license)

> **Note:** This package was created because existing screenshot solutions didn't work reliably on my Wayland setup.
> **Wayland MCP** provides screenshot, analysis, mouse and keyboard control tools for modern Linux desktops.

---

## ✨ Features

- **📸 Screenshot & Analysis**
  - Custom VLM integration for image analysis
  - Image comparison capabilities

- **🖱️ Input Simulation**
  - Mouse control (move, click, drag, scroll)
  - Keyboard input (typing, key presses)
  - Action chaining for complex sequences

---

## ⚠️ Security Warning

> **WARNING:** Enabling input control gives the MCP server full access to your mouse and keyboard.
> Only use with trusted MCP servers and models.

---

## 🚀 Quick Start

### 🔧 Input Control Setup
```bash
./setup.sh
```
[View setup.sh on GitHub](https://github.com/someaka/wayland-mcp/blob/main/setup.sh)

Configures permissions for `evemu-event` to control input devices.

### ⚙️ MCP Server Configuration
Add to your MCP server config (`.roo/mcp.json`):
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
        "DISPLAY": ":0",
        "WAYLAND_DISPLAY": "wayland-0",
        "XDG_SESSION_TYPE": "wayland"
      }
    }
  }
}
```

---

## 🛠️ Development
```bash
git clone https://github.com/someaka/wayland-mcp
cd wayland-mcp
pip install -e .
```

---

## 📜 License

GPL 3

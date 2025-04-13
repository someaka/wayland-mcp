# Wayland MCP Server (Work in Progress)

> **Note**: This package was created because existing screenshot solutions didn't work reliably on my Wayland setup. Key differentiators:

- Custom VLM integration for analysis
- Advanced input simulation:
  - [x] Typing, key presses, clicks
  - [x] Mouse dragging between coordinates
  - [ ] Vertical/horizontal scrolling
  - [ ] Cross-platform support

A Wayland screenshot and analysis tool with MCP (Model Control Protocol) integration.

## Features

- **Screen Capture and VLM Integration**: AI-powered screenshot analysis
- **MCP Tools**:
  - `capture_screenshot`: Fullscreen/region capture
  - `analyze_screenshot`: AI analysis of screenshots
  - `capture_and_analyze`: Combined capture+analysis
  - `compare_images`: Visual diff tool


## Input Control Setup

If you want the MCP server to control the mouse (e.g., with xdotool), you must set the correct XAUTHORITY environment variable so the server can authenticate with your X session.

**How to find your XAUTHORITY file:**

1. Open a terminal in your graphical session (e.g., VSCode terminal).
2. Run:

    echo $XAUTHORITY

This will print the path to your current X session's authority file. For example:

    /run/user/1000/.mutter-Xwaylandauth.XXXXXX

**How to set it in .roo/mcp.json:**

Add the following to the "env" section for your MCP server:

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
        "XAUTHORITY": "/run/user/1000/.mutter-Xwaylandauth.XXXXXX",
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

Replace the path with the value you found from the terminal.

This ensures the MCP server can authenticate with your X server and allows tools like xdotool to work from the server process, just as they do in your terminal.


## Development

```bash
git clone https://github.com/your-repo/wayland-mcp
cd wayland-mcp
pip install -e .
```

## License

GPT3

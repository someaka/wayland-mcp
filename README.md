# Wayland MCP Server (Work in Progress)

> **Note**: This package was created because existing screenshot solutions didn't work reliably on my Wayland setup. Key differentiators:

- Works consistently across Wayland and X11
- Minimal visual/sound disruption during capture
- Configurable timeouts for slower systems
- Custom VLM integration for analysis
- Advanced input simulation:
  - Typing, key presses, clicks
  - Mouse dragging between coordinates
  - Vertical/horizontal scrolling
  - Cross-platform support
- Clean, well-documented codebase

A robust Wayland screenshot and analysis tool with MCP (Model Control Protocol) integration.

## Input Control Options

This package offers mouse/keyboard control as an *optional* feature. The system will try these methods in order:

1. **Preferred**: python-evdev (no special permissions required if /dev/uinput is accessible)
   ```bash
   pip install evdev
   ```

2. **Fallback**: ydotool (requires admin permissions):
   ```bash
   sudo apt install ydotool
   sudo usermod -aG input $USER
   systemctl --user enable --now ydotoold
   ```

3. **X11 Systems**: PyAutoGUI will be used automatically

Note:
- Input control is not required for core screenshot and analysis functionality
- On Wayland, ensure your user has access to /dev/uinput for best results
- The python-evdev method is preferred as it doesn't require special permissions

## Features

- **Silent Screenshot Capture**: Minimal visual/sound disruption
- **Multi-Platform Support**: Works on X11 and Wayland
- **VLM Integration**: AI-powered screenshot analysis
- **MCP Tools**:
  - `capture_screenshot`: Silent fullscreen/region capture
  - `analyze_screenshot`: AI analysis of screenshots
  - `capture_and_analyze`: Combined capture+analysis
  - `compare_images`: Visual diff tool

## Installation

```bash
pip install wayland-mcp
```

## Configuration

1. Create `~/.roo/mcp.json`:
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
        "WAYLAND_MCP_PORT": "4999"
      }
    }
  }
}
```
### XAUTHORITY for X11/Wayland Mouse Control

If you want the MCP server to control the mouse (e.g., with xdotool), you must set the correct XAUTHORITY environment variable so the server can authenticate with your X session.

**How to find your XAUTHORITY file:**

1. Open a terminal in your graphical session (e.g., VSCode terminal).
2. Run:

    echo $XAUTHORITY

This will print the path to your current X session's authority file. For example:

    /run/user/1000/.mutter-Xwaylandauth.XXXXXX

**How to set it in .roo/mcp.json:**

Add the following to the "env" section for your MCP server:

    "XAUTHORITY": "/run/user/1000/.mutter-Xwaylandauth.XXXXXX"

Replace the path with the value you found from the terminal.

This ensures the MCP server can authenticate with your X server and allows tools like xdotool to work from the server process, just as they do in your terminal.


2. Set environment variables (optional):
```bash
export MCP_CONFIG_DIR=/path/to/config
```

## Usage

```python
from wayland_mcp import WaylandMCP

mcp = WaylandMCP()
result = mcp.capture_and_analyze("Describe this screenshot")
```

## Development

```bash
git clone https://github.com/your-repo/wayland-mcp
cd wayland-mcp
pip install -e .
```

## License

GPT3
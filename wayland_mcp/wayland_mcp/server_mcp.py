"""Wayland MCP server main entry point and MCP tool definitions.

This module initializes the FastMCP server, loads configuration and API keys,
and defines all MCP tools for screenshot capture, image analysis, and system actions.
"""

# pylint: disable=broad-exception-caught


import logging
import logging.handlers
import os
import json
import shutil
import subprocess
from fastmcp import FastMCP
from wayland_mcp.server.app import (
    capture_screenshot as capture_func,
    VLMAgent,
    compare_images as compare_func,
)
from .add_rulers import add_rulers
from .mouse_utils import MouseController

# Try to get API key from environment first
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# Fall back to config file if not in environment
if not OPENROUTER_API_KEY:

    def get_config_path() -> str:
        """Get config file path from environment or use default location

        Returns:
            str: Absolute path to config file
        """
        return os.path.join(
            os.environ.get("MCP_CONFIG_DIR", os.path.expanduser("~/.roo")), "mcp.json"
        )

    try:
        config_path = get_config_path()
        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)
            OPENROUTER_API_KEY = config["mcpServers"]["wayland-screenshot"]["env"][
                "OPENROUTER_API_KEY"
            ]
            logging.info(
                "API Key loaded from %s. First 8 chars: %s...", config_path, OPENROUTER_API_KEY[:8]
            )
    except FileNotFoundError:
        logging.warning("Config file not found at %s", config_path)
        OPENROUTER_API_KEY = ""
    except json.JSONDecodeError as e:
        logging.error("Invalid JSON in config file %s: %s", config_path, e)
        OPENROUTER_API_KEY = ""
    except KeyError as e:
        logging.error("Missing required key in config: %s", e)
        OPENROUTER_API_KEY = ""
    except OSError as e:
        logging.error("OS error loading config: %s", e)
        OPENROUTER_API_KEY = ""

# Initialize VLMAgent with the loaded key
vlm_agent = VLMAgent(OPENROUTER_API_KEY)
mouse = MouseController()
print(f"VLMAgent initialized with API key: {bool(vlm_agent.api_key)}")
# Print first 8 chars of API key if present (for debug)
if vlm_agent.api_key:
    print(f"Key first 8 chars: {vlm_agent.api_key[:8]}...")

# Get port configuration
try:
    PORT = int(os.environ.get("WAYLAND_MCP_PORT", "4999"))
except ValueError:
    PORT = 4999

# Configure logging to file
# File logging is disabled by default.
# To enable, uncomment the following lines:
# log_file = "mcp_server.log"
# log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
# log_handler = logging.FileHandler(log_file)
# log_handler.setFormatter(log_formatter)
# logging.getLogger().addHandler(log_handler)
logging.getLogger().setLevel(logging.INFO)  # Set desired log level

mcp = FastMCP("Wayland MCP")
logging.info("Initialized FastMCP server, will run on port %d.", PORT)


@mcp.tool()
def move_mouse(x: int, y: int) -> dict:
    """Move mouse to specified coordinates"""
    try:
        mouse.move_to(x, y)
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}

@mcp.tool()
def click_mouse() -> dict:
    """Simulate left mouse click (only left click supported)"""
    try:
        mouse.click()
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}

@mcp.tool()
def drag_mouse(x1: int, y1: int, x2: int, y2: int) -> dict:
    """Perform drag operation from (x1,y1) to (x2,y2)"""
    try:
        mouse.drag(x1, y1, x2, y2)
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}

@mcp.tool()
def scroll_mouse(amount: int) -> dict:
    """Scroll vertically (positive=up, negative=down)"""
    try:
        mouse.scroll(amount)
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}

@mcp.tool()
def capture_screenshot() -> dict[str, str | bool]:
    """Capture a screenshot of the current display with measurement rulers

    Returns:
        dict: {
            'success': bool,
            'filename': str if success,
            'error': str if not success
        }
    """
    # Use module-level logging

    logging.info("[MCP] capture_screenshot tool called")
    try:
        filename = "screenshot.png"
        result = capture_func(filename)
        if not isinstance(result, dict) or not result.get("success"):
            return {"success": False, "error": result.get("error", "Capture failed")}

        # Add measurement rulers
        try:
            ruled_filename = add_rulers(filename)
            return {"success": True, "filename": ruled_filename}
        except (OSError, IOError) as e:
            logging.error("Failed to add rulers: %s", e)
            return result  # Return original if ruler add fails

    # Catch-all for unexpected errors in screenshot capture (intentional for robustness)
    except (OSError, IOError, subprocess.CalledProcessError) as e:
        logging.error("[MCP] Exception in capture_screenshot: %s", e)
        return {"success": False, "error": f"Exception in MCP tool: {e}"}
    # Duplicate except for demonstration; can be removed or merged
    # except Exception as e:
    #     logging.error("[MCP] Exception in capture_screenshot: %s", e)
    #     return {"success": False, "error": f"Exception in MCP tool: {e}"}
    finally:
        logging.info("[MCP] capture_screenshot tool exit")


@mcp.tool()
def compare_images(img1_path: str, img2_path: str) -> bool:
    """Compare two images for equality.

    Args:
        img1_path (str): Path to the first image.
        img2_path (str): Path to the second image.

    Returns:
        bool: True if images are equal, False otherwise.
    """
    return compare_func(img1_path, img2_path)


@mcp.tool()
def analyze_screenshot(image_path: str, prompt: str) -> str:
    """Analyze a screenshot using VLM

    Args:
        image_path: Path to screenshot image
        prompt: Analysis instructions for VLM

    Returns:
        str: Analysis result or error message
    """
    result = vlm_agent.analyze_screenshot(image_path, prompt)
    return result or ""

def _handle_type_action(text: str) -> bool:
    """Handle typing text using wtype."""
    if shutil.which("wtype"):
        subprocess.run(["wtype", text], check=True)
        return True
    logging.error(
        "wtype not found - install with:\n"
        "  Debian/Ubuntu: sudo apt install wtype\n"
        "  Arch: sudo pacman -S wtype\n"
        "Or build from source: https://github.com/atx/wtype"
    )
    return False

def _handle_press_action(key: str) -> bool:
    """Handle key press using wtype."""
    if shutil.which("wtype"):
        subprocess.run(["wtype", "-k", key], check=True)
        return True
    logging.error(
        "wtype not found - install with:\n"
        "  Debian/Ubuntu: sudo apt install wtype\n"
        "  Arch: sudo pacman -S wtype\n"
        "Or build from source: https://github.com/atx/wtype"
    )
    return False

def _handle_click_action(action: str) -> bool:
    """Handle mouse click using ydotool for Wayland."""
    # Validate coordinates
    coords = _parse_click_coordinates(action)
    if not coords:
        return False

    # Try ydotool first (Wayland compatible)
    if shutil.which("ydotool"):
        try:
            subprocess.run(
                [
                    "ydotool", "mousemove", "--absolute",
                    "--x", str(coords[0]), "--y", str(coords[1])
                ],
                check=True,
                timeout=5
            )
            return True
        except Exception as e:
            logging.error("ydotool failed: %s", e)

    # Fallback to xdotool for X11
    if shutil.which("xdotool"):
        env = _prepare_x11_environment()
        if env:
            return _execute_click_command(coords[0], coords[1], env)

    logging.error(
        "No compatible mouse control tool found "
        "(install ydotool for Wayland or xdotool for X11)"
    )
    return False

def _parse_click_coordinates(action: str) -> tuple[int, int] | None:
    """Parse and validate click coordinates from action string."""
    try:
        x, y = map(int, action[6:].split(","))
        if x < 0 or y < 0:
            logging.error("Invalid coordinates: %d,%d - must be positive", x, y)
            return None
        return (x, y)
    except ValueError as e:
        logging.error("Invalid coordinate format: %s", e)
        return None

def _prepare_x11_environment() -> dict | None:
    """Prepare X11 environment variables for xdotool execution."""
    env = os.environ.copy()

    # Handle DISPLAY variable
    if "DISPLAY" not in env:
        if os.path.exists("/tmp/.X11-unix/X0"):
            env["DISPLAY"] = ":0"
            logging.info("DISPLAY not set, defaulting to :0")
        else:
            logging.error("DISPLAY not set and no default found at /tmp/.X11-unix/X0")
            return None

    # Handle XAUTHORITY variable
    if "XAUTHORITY" not in env:
        default_xauth = os.path.expanduser("~/.Xauthority")
        if os.path.exists(default_xauth):
            env["XAUTHORITY"] = default_xauth
            logging.info("Using default XAUTHORITY: %s", default_xauth)

    return env

def _execute_click_command(x: int, y: int, env: dict) -> bool:
    """Execute the xdotool command with prepared environment."""
    command = [
        "xdotool", "mousemove", str(x), str(y),
        "sleep", "0.1", "click", "1"
    ]

    try:
        result = subprocess.run(
            command,
            env=env,
            check=True,
            capture_output=True,
            text=True,
            timeout=5  # Add timeout to prevent hanging
        )
        logging.info("xdotool executed successfully. Output: %s", result.stdout)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        logging.error("xdotool command failed: %s", e)
        if hasattr(e, "stderr") and e.stderr:
            logging.error("Command error: %s", e.stderr)
        return False

def _handle_drag_action(action: str) -> bool:
    """Handle mouse drag using xdotool."""
    coords = action[5:].split(":")
    if len(coords) != 2:
        logging.error("Drag action requires start and end coordinates")
        return False
    try:
        x1, y1 = map(int, coords[0].split(","))
        x2, y2 = map(int, coords[1].split(","))
    except ValueError as e:
        logging.error("Invalid coordinate format: %s", e)
        return False

    # Check for xdotool installation
    if not shutil.which("xdotool"):
        logging.error("xdotool not found - install with: sudo apt install xdotool")
        return False

    # Prepare execution environment
    env = _prepare_x11_environment()
    if not env:
        return False

    # Execute drag command sequence with delays
    command = [
        "xdotool", "mousemove", str(x1), str(y1),
        "sleep", "0.2", "mousedown", "1",
        "sleep", "0.2", "mousemove", str(x2), str(y2),
        "sleep", "0.2", "mouseup", "1"
    ]

    try:
        subprocess.run(
            command,
            env=env,
            check=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        logging.info("xdotool drag executed successfully")
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        logging.error("xdotool drag command failed: %s", e)
        if hasattr(e, "stderr") and e.stderr:
            logging.error("Command error: %s", e.stderr)
        return False


@mcp.tool()
def execute_action(action: str) -> bool:
    """Execute system actions like key presses or mouse clicks

    Args:
        action: Action string in format "type:text" or "press:key" or "click:x,y"

    Returns:
        bool: True if successful, False otherwise
    """
    handlers = {
        "type:": lambda: _handle_type_action(action[5:]),
        "press:": lambda: _handle_press_action(action[6:]),
        "click:": lambda: _handle_click_action(action),
        "drag:": lambda: _handle_drag_action(action)
    }

    try:
        if not action or not isinstance(action, str):
            logging.error("Invalid action: None or not a string")
            return False

        for prefix, handler in handlers.items():
            if action.startswith(prefix):
                return handler()

        logging.error("Unknown action format: %s", action)
        return False

    except (ValueError, subprocess.CalledProcessError) as e:
        logging.error("Action execution failed: %s", e)
        return False


@mcp.tool()
def capture_and_analyze(prompt: str) -> dict:
    """Capture a screenshot and analyze it with VLM.

    Args:
        prompt (str): Analysis instructions for VLM.

    Returns:
        dict: {
            'success': bool,
            'filename': str,
            'analysis': str,
            'filesize': int,
            'error': str (if any)
        }
    """
    try:
        # Capture screenshot
        result = capture_screenshot()
        if not result.get("success"):
            return {"success": False, "error": result.get("error", "Capture failed")}

        # Verify file exists
        filename = result["filename"]
        if not os.path.exists(filename):
            return {"success": False, "error": "Screenshot file not found"}

        # Analyze screenshot
        analysis = vlm_agent.analyze_screenshot(filename, prompt)
        return {
            "success": True,
            "filename": filename,
            "analysis": analysis,
            "filesize": os.path.getsize(filename),
        }
    # Catch-all for unexpected errors in capture and analyze (intentional for robustness)
    except (OSError, IOError, ValueError) as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    logging.info("Starting MCP server...")
    try:
        mcp.run()
        logging.info("MCP server running on port %d", PORT)
    # Catch-all for unexpected errors in server run (intentional for robustness)
    except RuntimeError as e:
        logging.error("Failed to start MCP server: %s", e)


def main():
    """Entry point for running the MCP server as a script."""
    logging.info("Starting MCP server via main()...")
    try:
        mcp.run()
        logging.info("MCP server running on port %d", PORT)
    except RuntimeError as e:
        logging.error("Failed to start MCP server: %s", e)

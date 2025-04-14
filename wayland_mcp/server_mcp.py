"""Wayland MCP server main entry point and MCP tool definitions.
This module provides:
- FastMCP server initialization
- Configuration and API key loading
- MCP tool definitions for:
  * Screenshot capture with measurement rulers
  * Image comparison and analysis
  * Mouse control (move, click, drag, scroll)
  * System action execution
- Main server entry point and execution
"""
# pylint: disable=broad-exception-caught
import logging
import logging.handlers
import os
import json
import shutil
import subprocess
import time
from fastmcp import FastMCP  # pylint: disable=import-error
from wayland_mcp.app import (
    capture_screenshot as capture_func,
    VLMAgent,
)
from wayland_mcp.add_rulers import add_rulers
from wayland_mcp.mouse_utils import MouseController
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
                "API Key loaded from %s. First 8 chars: %s...",
                config_path,
                OPENROUTER_API_KEY[:8],
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
LOG_FILE = "/tmp/wayland-mcp.log"
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler = logging.FileHandler(LOG_FILE)
log_handler.setFormatter(log_formatter)
logging.getLogger().addHandler(log_handler)
logging.getLogger().setLevel(logging.INFO)  # Set desired log level
mcp = FastMCP("Wayland MCP")
logging.info("Initialized FastMCP server, will run on port %d.", PORT)
@mcp.tool()
def move_mouse(x: int, y: int) -> dict:
    """Move mouse to specified coordinates"""
    try:
        mouse.move_to(x, y)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
@mcp.tool()
def click_mouse() -> dict:
    """Simulate left mouse click (only left click supported)"""
    try:
        mouse.click()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
@mcp.tool()
def drag_mouse(x1: int, y1: int, x2: int, y2: int) -> dict:
    """Perform drag operation from (x1,y1) to (x2,y2)"""
    try:
        mouse.drag(x1, y1, x2, y2)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
@mcp.tool()
def scroll_mouse(amount: int) -> dict:
    """Scroll vertically (positive=up, negative=down)"""
    try:
        mouse.scroll(amount)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
@mcp.tool()
def capture_screenshot(filename: str = "screenshot.png") -> dict[str, str | bool]:
    """Capture a screenshot of the current display with measurement rulers
    Args:
        filename (str, optional): The filename to save the screenshot as.
            Defaults to "screenshot.png".
    Returns:
        dict: {
            'success': bool,
            'filename': str if success,
            'error': str if not success
        }
    """
    logging.info("[MCP] capture_screenshot tool called")
    try:
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
    except (OSError, IOError, subprocess.CalledProcessError) as e:
        logging.error("[MCP] Exception in capture_screenshot: %s", e)
        return {"success": False, "error": f"Exception in MCP tool: {e}"}
    finally:
        logging.info("[MCP] capture_screenshot tool exit")
@mcp.tool()
def compare_images(img1_path: str, img2_path: str) -> dict:
    """
    Compare two images for equality using the configured Vision-Language Model (VLM).
    Args:
        img1_path (str): Path to the first image.
        img2_path (str): Path to the second image.
    Returns:
        dict: {
            'success': bool,
            'equal': str (description or result),
            'error': str (if any)
        }
    """
    try:
        logging.info("Received compare_images request for:\n- %s\n- %s", img1_path, img2_path)
        # Convert to absolute paths
        abs_img1 = os.path.abspath(img1_path)
        abs_img2 = os.path.abspath(img2_path)
        # Verify both files exist with debug info
        logging.info("Checking image 1 at: %s", abs_img1)
        if not os.path.exists(abs_img1):
            logging.error("Image 1 not found at: %s", abs_img1)
            return {"success": False, "error": f"Image not found: {abs_img1}"}
        logging.info("Checking image 2 at: %s", abs_img2)
        if not os.path.exists(abs_img2):
            logging.error("Image 2 not found at: %s", abs_img2)
            return {"success": False, "error": f"Image not found: {abs_img2}"}
        logging.info("Both images found, proceeding with comparison")
        # Read and log first few bytes of each image
        with open(abs_img1, 'rb') as file1:
            img1_head = file1.read(16)
            logging.debug("Image 1 header: %s", img1_head)
        with open(abs_img2, 'rb') as file2:
            img2_head = file2.read(16)
            logging.debug("Image 2 header: %s", img2_head)
        try:
            result = vlm_agent.compare_images(abs_img1, abs_img2)
            logging.info("Comparison completed successfully")
            logging.debug("Full comparison result: %s", result)
            return {"success": True, "equal": result}
        except Exception as e:
            logging.error("Comparison failed: %s", str(e), exc_info=True)
            return {"success": False, "error": str(e)}
    except Exception as e:
        logging.error("Image comparison failed: %s", e)
        return {"success": False, "error": str(e)}
@mcp.tool()
def analyze_screenshot(image_path: str, prompt: str) -> str:
    """
    Analyze a screenshot using the configured Vision-Language Model (VLM).
    Args:
        image_path: Path to screenshot image
        prompt: Analysis instructions for VLM
    Returns:
        str: Analysis result or error message
    """
    return vlm_agent.analyze_image(image_path, prompt) or ""
# Key event mapping for typing
KEY_MAP = {
    "a": "KEY_A", "b": "KEY_B", "c": "KEY_C", "d": "KEY_D", "e": "KEY_E",
    "f": "KEY_F", "g": "KEY_G", "h": "KEY_H", "i": "KEY_I", "j": "KEY_J",
    "k": "KEY_K", "l": "KEY_L", "m": "KEY_M", "n": "KEY_N", "o": "KEY_O",
    "p": "KEY_P", "q": "KEY_Q", "r": "KEY_R", "s": "KEY_S", "t": "KEY_T",
    "u": "KEY_U", "v": "KEY_V", "w": "KEY_W", "x": "KEY_X", "y": "KEY_Y",
    "z": "KEY_Z", " ": "KEY_SPACE", "\n": "KEY_ENTER",
    "0": "KEY_0", "1": "KEY_1", "2": "KEY_2", "3": "KEY_3", "4": "KEY_4",
    "5": "KEY_5", "6": "KEY_6", "7": "KEY_7", "8": "KEY_8", "9": "KEY_9"
}
def _send_key(evemu_dev: str, keycode: str) -> bool:
    """Send a key press and release event."""
    try:
        # Press
        subprocess.run(
            ["evemu-event", evemu_dev, "--type", "EV_KEY", "--code", keycode, "--value", "1"],
            check=True
        )
        subprocess.run(
            ["evemu-event", evemu_dev, "--type", "EV_SYN", "--code", "SYN_REPORT", "--value", "0"],
            check=True
        )
        # Release
        subprocess.run(
            ["evemu-event", evemu_dev, "--type", "EV_KEY", "--code", keycode, "--value", "0"],
            check=True
        )
        subprocess.run(
            ["evemu-event", evemu_dev, "--type", "EV_SYN", "--code", "SYN_REPORT", "--value", "0"],
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        logging.error("Failed to send key %s: %s", keycode, e)
        return False
def _find_keyboard_device() -> str:
    """Find a writable keyboard event device."""
    for event in os.listdir("/dev/input"):
        if event.startswith("event"):
            dev_path = f"/dev/input/{event}"
            try:
                desc = subprocess.check_output(["evemu-describe", dev_path], text=True, timeout=1)
                if "KEY_A" in desc and "KEY_ENTER" in desc:
                    return dev_path
            except Exception:
                continue
    return ""
def _handle_type_action(text: str) -> bool:
    """Handle typing text using evemu-event."""
    keyboard_dev = _find_keyboard_device()
    if not keyboard_dev:
        logging.error("No keyboard device found")
        return False
    for char in text.lower():
        keycode = KEY_MAP.get(char)
        if keycode:
            if not _send_key(keyboard_dev, keycode):
                return False
            time.sleep(0.05)  # Small delay between keystrokes
    return True
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
                    "ydotool",
                    "mousemove",
                    "--absolute",
                    "--x",
                    str(coords[0]),
                    "--y",
                    str(coords[1]),
                ],
                check=True,
                timeout=5,
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
    command = ["xdotool", "mousemove", str(x), str(y), "sleep", "0.1", "click", "1"]
    try:
        result = subprocess.run(
            command,
            env=env,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,  # Add timeout to prevent hanging
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
        "xdotool",
        "mousemove",
        str(x1),
        str(y1),
        "sleep",
        "0.2",
        "mousedown",
        "1",
        "sleep",
        "0.2",
        "mousemove",
        str(x2),
        str(y2),
        "sleep",
        "0.2",
        "mouseup",
        "1",
    ]
    try:
        subprocess.run(
            command, env=env, check=True, capture_output=True, text=True, timeout=5
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
        "drag:": lambda: _handle_drag_action(action),
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
    # Catch-all for unexpected errors in capture and analyze
    # (intentional for robustness)
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

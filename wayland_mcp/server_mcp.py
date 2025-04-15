"""Wayland MCP server with action chaining support.
Provides tools for:
- Mouse control (move, click, drag, scroll)
- Keyboard input (typing, key presses)
- Screenshot capture and analysis
- Action chaining (combining multiple actions)
Tool Usage:
All tools are accessible via the MCP protocol using the @mcp.tool() decorator.
Tools can be called individually or chained together.
Action Chaining Syntax:
  chain:action1;action2;action3
Where actions are in format:
  type:text
  press:key
  click:x,y
  drag:x1,y1:x2,y2
Example Chains:
  chain:click:100,200;type:hello;press:Enter
  chain:drag:50,50:100,100;click:200,200
"""
import logging
import os
import json
from typing import Optional, Tuple
from fastmcp import FastMCP
from wayland_mcp.chain_processor import ChainProcessor, register_handler
from wayland_mcp.mouse_utils import MouseController
from wayland_mcp.keyboard_utils import KeyboardController
from wayland_mcp.screen_utils import ScreenController
from wayland_mcp.app import VLMAgent
# Configuration setup
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
# Fall back to config file if not in environment
if not OPENROUTER_API_KEY:
    def get_config_path() -> str:
        """Get config file path from environment or default location."""
        return os.path.join(
            os.environ.get("MCP_CONFIG_DIR", os.path.expanduser("~/.roo")),
            "mcp.json"
        )
    try:
        with open(get_config_path(), encoding="utf-8") as f:
            OPENROUTER_API_KEY = json.load(f)[
                "mcpServers"]["wayland-screenshot"]["env"]["OPENROUTER_API_KEY"
            ]
    except (json.JSONDecodeError, KeyError, IOError) as e:
        logging.error("Failed to load API key: %s", e)
        OPENROUTER_API_KEY = ""
# Initialize core components using MouseController's built-in detection
mouse = MouseController()
logging.info("Initialized MouseController with device: %s", mouse.device)
keyboard = KeyboardController()
screen = ScreenController(VLMAgent(OPENROUTER_API_KEY))
# Server configuration
try:
    PORT = int(os.environ.get("WAYLAND_MCP_PORT", "4999"))
except ValueError:
    PORT = 4999
# Logging setup
LOG_FILE = "/tmp/wayland-mcp.log"
log_handler = logging.FileHandler(LOG_FILE)
log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(log_handler)
logging.getLogger().setLevel(logging.INFO)
mcp = FastMCP("Wayland MCP")
logging.info("Initialized FastMCP server on port %d", PORT)
# Mouse control tools
@mcp.tool()
def move_mouse(x: int, y: int, relative: bool = False) -> dict:
    """Move mouse to specified screen coordinates.
    Args:
        x: Horizontal position (0 = left)
        y: Vertical position (0 = top)
        relative: If True, moves relative to current position (default: False)
    Returns:
        dict: {
            'success': bool,
            'error': str (if failed)
        }
    Examples:
        move_mouse(100, 200)  # Moves to absolute x=100, y=200
        move_mouse(10, 10, relative=True)  # Moves 10px right and down
    """
    try:
        if relative:
            mouse.move_to(x, y)
        else:
            print("Moving to absolute coordinates")
            print(f"Moving to x={x}, y={y}")
            mouse.move_to_absolute(x, y)
        return {"success": True}
    except (RuntimeError, IOError) as e:
        return {"success": False, "error": str(e)}
@mcp.tool()
def click_mouse() -> dict:
    """Simulate left mouse click at current position.
    Returns:
        dict: {
            'success': bool,
            'error': str (if failed)
        }
    Example:
        click_mouse()  # Clicks at current cursor position
    """
    try:
        mouse.click()
        return {"success": True}
    except (RuntimeError, IOError) as e:
        return {"success": False, "error": str(e)}
@mcp.tool()
def drag_mouse(x1: int, y1: int, x2: int, y2: int) -> dict:
    """Perform drag operation between coordinates.
    Args:
        x1, y1: Start position
        x2, y2: End position
    Returns:
        dict: {
            'success': bool,
            'error': str (if failed)
        }
    Example:
        drag_mouse(100, 100, 200, 200)  # Drags from (100,100) to (200,200)
    """
    try:
        mouse.drag(x1, y1, x2, y2)
        return {"success": True}
    except (RuntimeError, IOError) as e:
        return {"success": False, "error": str(e)}
@mcp.tool()
def scroll_mouse(amount: int) -> dict:
    """Scroll vertically (positive=up, negative=down).
    Note: Each unit represents one notch on the scroll wheel (120 units = high-definition scroll).
    Typical values range from 2-3 to 5-10 for normal scrolling.
    """
    try:
        mouse.scroll(amount)
        return {"success": True}
    except (RuntimeError, IOError) as e:
        return {"success": False, "error": str(e)}
# Media capture tools
@mcp.tool()
def capture_screenshot(filename: str = "screenshot.png") -> dict:
    """Capture screenshot with measurement rulers."""
    return screen.capture(filename)
@mcp.tool()
def compare_images(img1_path: str, img2_path: str) -> dict:
    """Compare two images using VLM."""
    return screen.compare(img1_path, img2_path)
@mcp.tool()
def analyze_screenshot(image_path: str, prompt: str) -> str:
    """Analyze screenshot using VLM."""
    result = screen.analyze(image_path, prompt)
    return result.get("analysis", "") if result.get("success") else ""
def _handle_type_action(text: str) -> dict:
    """Handle typing text using KeyboardController."""
    try:
        success = keyboard.type_text(text)
        return {"success": success, "error": "" if success else "Type action failed"}
    except (RuntimeError, ValueError) as e:
        logging.error("Type action failed: %s", e)
        return {"success": False, "error": str(e)}
def _handle_press_action(key: str) -> dict:
    """Handle key press using KeyboardController."""
    try:
        success = keyboard.press_key(key)
        return {"success": success, "error": "" if success else "Press action failed"}
    except (RuntimeError, ValueError) as e:
        logging.error("Press action failed: %s", e)
        return {"success": False, "error": str(e)}
def _handle_scroll_action(action: str) -> dict:
    """Handle scroll action.
    Args:
        action: Should be "scroll:amount" where amount is an integer
        Note:
          - Each unit = 1 scroll notch (120 = high-def scroll)
          - Typical values: 15-120 for normal scrolling
    """
    if len(action) <= 7 or not action.startswith("scroll:"):
        return {"success": False, "error": "Bad scroll format"}
    try:
        amount_str = action[7:]
        if not amount_str:
            return {"success": False, "error": "Missing scroll amount"}
        amount = int(amount_str)
        mouse.scroll(amount)
        return {"success": True}
    except ValueError:
        return {"success": False, "error": "Scroll amount must be a number"}
    except RuntimeError as e:
        logging.error("Scroll action failed: %s", e)
        return {"success": False, "error": str(e)}
def _handle_click_action() -> dict:
    """Handle click action at current mouse position."""
    try:
        mouse.click()
        return {"success": True}
    except (RuntimeError, ValueError) as e:
        logging.error("Click action failed: %s", e)
        return {"success": False, "error": str(e)}
def _handle_move_to_action(coords_str) -> dict:
    """Handle move to coordinates (absolute or relative).
    Args:
        coords_str: The coordinates string in format:
          - "x,y" for absolute movement (e.g. "500,500")
          - "rel:x,y" for relative movement (e.g. "rel:10,-5")
    """
    try:
        relative = coords_str.startswith("rel:")
        if relative:
            coords_str = coords_str[4:]
        coords = _parse_coordinates(coords_str)
        if not coords:
            return {"success": False, "error": "Invalid coordinates"}
        if relative:
            mouse.move_to(*coords)
        else:
            mouse.move_to_absolute(*coords)
        return {"success": True}
    except (RuntimeError, ValueError) as e:
        logging.error("Move to action failed: %s", e)
        return {"success": False, "error": str(e)}
def _handle_drag_action(action: str) -> dict:
    """Handle drag action between coordinates."""
    parts = action[5:].split(":")
    if len(parts) != 2:
        return {"success": False, "error": "Invalid drag format"}
    start = _parse_coordinates(parts[0])
    end = _parse_coordinates(parts[1])
    if not start or not end:
        return {"success": False, "error": "Invalid coordinates"}
    try:
        mouse.drag(*start, *end)
        return {"success": True}
    except (RuntimeError, ValueError) as e:
        logging.error("Drag action failed: %s", e)
        return {"success": False, "error": str(e)}
def _parse_coordinates(coords_str: str) -> Optional[Tuple[int, int]]:
    """Parse x,y coordinates from string."""
    try:
        x, y = map(int, coords_str.split(","))
        if x < 0 or y < 0:
            raise ValueError("Coordinates must be positive")
        return (x, y)
    except ValueError as e:
        logging.error("Invalid coordinates: %s", e)
        return None
# Register action handlers with proper parameter passing
def make_handler(prefix: str, handler: callable) -> callable:
    """Create an action handler that strips the prefix.
    Args:
        prefix: The action prefix to strip
        handler: The handler function to call
    Returns:
        A function that processes the action after the prefix
    """
    return lambda action: handler(action[len(prefix):])
register_handler("type:", lambda action: _handle_type_action(action[5:]))
register_handler("press:", make_handler("press:", _handle_press_action))
register_handler("click", lambda _: _handle_click_action())
register_handler("click:", lambda _: _handle_click_action())
register_handler("move_to:", lambda action: _handle_move_to_action(coords_str=action[8:]))
register_handler("drag:", make_handler("drag:", _handle_drag_action))
register_handler("scroll:", _handle_scroll_action)
@mcp.tool()
def execute_action(action: str) -> bool:
    """Execute system actions with chaining support.
    Handles both single actions and chained sequences.
    Args:
        action: Action string in format:
          Single: "prefix:params" (e.g. "click:100,200")
          Chain: "chain:action1;action2" (e.g. "chain:click:100,200;type:hello")
    Supported Actions:
      type:text - Type text
      press:key - Press key
      click/click: - Click at current position (both formats supported)
      move_to:x,y - Move to absolute coordinates (default)
      move_to:rel:x,y - Move relative to current position
      drag:x1,y1:x2,y2 - Drag between points
      scroll:amount - Vertical scroll (positive=up, negative=down)
        Note: Each unit = 1 scroll notch (120 = high-def scroll). Typical: 15-120.
      scroll:horizontal:amount - Horizontal scroll
        Note: Each unit = 1 scroll notch (120 = high-def scroll). Typical: 15-120.
    Returns:
        bool: True if all actions succeeded, False otherwise
    Example:
        execute_action("click:100,200")
        execute_action("chain:click:100,200;type:hello;press:Enter")
    """
    handlers = {
        "chain:": lambda: ChainProcessor(action[6:]).execute(),
        "type:": _handle_type_action,
        "press:": _handle_press_action,
        "click": _handle_click_action,
        "move_to:": lambda: _handle_move_to_action(action[8:]),
        "drag:": _handle_drag_action,
        "scroll:": _handle_scroll_action,
    }
    if not action or not isinstance(action, str):
        logging.error("Invalid action")
        return {"success": False, "error": "Invalid action"}
    for prefix, handler in handlers.items():
        if action.startswith(prefix):
            try:
                result = handler()
                if isinstance(result, bool):  # Backward compatibility
                    return {"success": result, "error": "" if result else "Action failed"}
                return result
            except (RuntimeError, ValueError, IOError) as e:
                logging.error("Action failed: %s", e)
                return {"success": False, "error": str(e)}
    logging.error("Unknown action format: %s", action)
    return {"success": False, "error": "Unknown action format"}
@mcp.tool()
def capture_and_analyze(prompt: str) -> dict:
    """Capture and analyze screenshot."""
    return screen.capture_and_analyze(prompt)
# Server entry points
if __name__ == "__main__":
    try:
        mcp.run()
        logging.info("MCP server running on port %d", PORT)
    except (RuntimeError, IOError) as e:
        logging.error("Server failed: %s", e)
def main():
    """Script entry point."""
    try:
        mcp.run()
        logging.info("MCP server running on port %d", PORT)
    except RuntimeError as e:
        logging.error("Server failed: %s", e)

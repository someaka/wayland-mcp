import logging
import logging.handlers
import os
import json
import shutil
import subprocess
import dbus
from fastmcp import FastMCP
from wayland_mcp.server.app import capture_screenshot as capture_func, VLMAgent, compare_images as compare_func
from .add_rulers import add_rulers

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
            os.environ.get('MCP_CONFIG_DIR', os.path.expanduser('~/.roo')),
            'mcp.json'
        )

    try:
        config_path = get_config_path()
        with open(config_path) as f:
            config = json.load(f)
            OPENROUTER_API_KEY = config['mcpServers']['wayland-screenshot']['env']['OPENROUTER_API_KEY']
            logging.info(f"API Key loaded from {config_path}. First 8 chars: {OPENROUTER_API_KEY[:8]}...")
    except FileNotFoundError:
        logging.warning(f"Config file not found at {config_path}")
        OPENROUTER_API_KEY = ""
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in config file {config_path}: {e}")
        OPENROUTER_API_KEY = ""
    except KeyError as e:
        logging.error(f"Missing required key in config: {e}")
        OPENROUTER_API_KEY = ""
    except Exception as e:
        logging.error(f"Error loading config: {e}")
        OPENROUTER_API_KEY = ""

# Initialize VLMAgent with the loaded key
vlm_agent = VLMAgent(OPENROUTER_API_KEY)
print(f"VLMAgent initialized with API key: {bool(vlm_agent.api_key)}")
print(f"Key first 8 chars: {vlm_agent.api_key[:8]}...") if vlm_agent.api_key else None

# Get port configuration
try:
    PORT = int(os.environ.get("WAYLAND_MCP_PORT", "4999"))
except ValueError:
    PORT = 4999

# Configure logging to file
log_file = "mcp_server.log"
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler = logging.FileHandler(log_file)
log_handler.setFormatter(log_formatter)
logging.getLogger().addHandler(log_handler)
logging.getLogger().setLevel(logging.INFO) # Set desired log level

mcp = FastMCP("Wayland MCP")
logging.info(f"Initialized FastMCP server, will run on port {PORT}. Logging to {log_file}")

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
    import logging
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
        except Exception as e:
            logging.error(f"Failed to add rulers: {e}")
            return result  # Return original if ruler add fails
            
    except Exception as e:
        logging.error(f"[MCP] Exception in capture_screenshot: {e}")
        return {"success": False, "error": f"Exception in MCP tool: {e}"}
    except Exception as e:
        logging.error(f"[MCP] Exception in capture_screenshot: {e}")
        return {"success": False, "error": f"Exception in MCP tool: {e}"}
    finally:
        logging.info("[MCP] capture_screenshot tool exit")

@mcp.tool()
def compare_images(img1_path: str, img2_path: str) -> bool:
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

@mcp.tool()
def execute_action(action: str) -> bool:
    """Execute system actions like key presses or mouse clicks
    
    Args:
        action: Action string in format "type:text" or "press:key" or "click:x,y"
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not action or not isinstance(action, str):
            logging.error("Invalid action: None or not a string")
            return False
            
        if action.startswith("type:"):
            text = action[5:]
            if shutil.which("wtype"):
                subprocess.run(["wtype", text], check=True)
            else:
                logging.error("wtype not found - install with:\n"
                            "  Debian/Ubuntu: sudo apt install wtype\n"
                            "  Arch: sudo pacman -S wtype\n"
                            "Or build from source: https://github.com/atx/wtype")
                return False
            return True

        elif action.startswith("press:"):
            key = action[6:]
            if shutil.which("wtype"):
                subprocess.run(["wtype", "-k", key], check=True)
            else:
                logging.error("wtype not found - install with:\n"
                            "  Debian/Ubuntu: sudo apt install wtype\n"
                            "  Arch: sudo pacman -S wtype\n"
                            "Or build from source: https://github.com/atx/wtype")
                return False
            return True
            
        elif action.startswith("click:"):
            try:
                x, y = map(int, action[6:].split(","))
                if x < 0 or y < 0:
                    logging.error(f"Invalid coordinates: {x},{y} - must be positive")
                    return False
            except ValueError as e:
                logging.error(f"Invalid coordinate format: {e}")
                return False

            try:
                if not shutil.which("xdotool"):
                    logging.error("xdotool not found - install with: sudo apt install xdotool")
                    return False

                # Ensure DISPLAY and XAUTHORITY are set for xdotool
                env = os.environ.copy()
                if 'DISPLAY' not in env:
                    # Attempt to find the display if not set (common for services)
                    try:
                        # Check common display locations
                        if os.path.exists("/tmp/.X11-unix/X0"):
                            env['DISPLAY'] = ':0'
                            logging.info("DISPLAY not set, setting to :0")
                        else:
                            # Fallback or further logic needed if :0 doesn't exist
                            logging.warning("DISPLAY not set and default :0 not found.")
                            # Consider trying other display numbers if necessary
                    except Exception as find_disp_e:
                        logging.error(f"Error trying to determine DISPLAY: {find_disp_e}")

                # Ensure XAUTHORITY is set, defaulting to standard user location
                if 'XAUTHORITY' not in env:
                    default_xauthority = os.path.expanduser("~/.Xauthority")
                    if os.path.exists(default_xauthority):
                        env['XAUTHORITY'] = default_xauthority
                        logging.info(f"XAUTHORITY not set, using default: {env['XAUTHORITY']}")
                    else:
                        logging.warning(f"XAUTHORITY not set and default file not found: {default_xauthority}")
                else:
                     logging.info(f"Using existing XAUTHORITY: {env['XAUTHORITY']}")

                if 'DISPLAY' not in env:
                     logging.error("Cannot execute xdotool: DISPLAY environment variable is not set.")
                     return False # Cannot proceed without a display
                
                # Construct the xdotool command sequence with a small delay
                command = [
                    "xdotool",
                    "mousemove", str(x), str(y),
                    "sleep", "0.1",  # Add a 100ms delay
                    "click", "1"     # Button 1 = left click
                ]
                
                logging.info(f"Executing xdotool command: {' '.join(command)}")
                
                # Run xdotool with error checking and capture output
                result = subprocess.run(
                    command,
                    env=env,
                    check=True,  # Re-enable error checking
                    capture_output=True,
                    text=True
                )
                logging.info(f"xdotool executed successfully. Output: {result.stdout}")
                return True
            except subprocess.CalledProcessError as e:
                logging.error(f"xdotool command failed with exit code {e.returncode}")
                logging.error(f"Command: {' '.join(e.cmd)}")
                logging.error(f"Stderr: {e.stderr}")
                return False
            except Exception as e:
                logging.error(f"xdotool execution failed with unexpected error: {str(e)}")
                return False
            
        elif action.startswith("drag:"):
            coords = action[5:].split(":")
            if len(coords) != 2:
                logging.error("Drag action requires start and end coordinates")
                return False
                
            x1, y1 = map(int, coords[0].split(","))
            x2, y2 = map(int, coords[1].split(","))
            
            if shutil.which("wlrctl"):
                subprocess.run(["wlrctl", "pointer", "move", str(x1), str(y1)], check=True)
                subprocess.run(["wlrctl", "pointer", "button", "left", "press"], check=True)
                subprocess.run(["wlrctl", "pointer", "move", str(x2), str(y2)], check=True)
                subprocess.run(["wlrctl", "pointer", "button", "left", "release"], check=True)
            else:
                logging.error("wlrctl not found - install with:\n"
                            "  Debian/Ubuntu: sudo apt install wlrctl\n"
                            "  Arch: sudo pacman -S wlrctl\n"
                            "Or build from source: https://github.com/emersion/wlrctl")
                return False
            return True
            
        logging.error(f"Unknown action format: {action}")
        return False
        
    except Exception as e:
        logging.error(f"Action execution failed: {e}")
        return False

@mcp.tool()
def capture_and_analyze(prompt: str) -> dict:
    """Capture screenshot and analyze it with VLM"""
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
            "filesize": os.path.getsize(filename)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    logging.info("Starting MCP server...")
    try:
        mcp.run()
        logging.info(f"MCP server running on port {PORT}")
    except Exception as e:
        logging.error(f"Failed to start MCP server: {e}")

def main():
    logging.info("Starting MCP server via main()...")
    try:
        mcp.run()
        logging.info(f"MCP server running on port {PORT}")
    except Exception as e:
        logging.error(f"Failed to start MCP server: {e}")

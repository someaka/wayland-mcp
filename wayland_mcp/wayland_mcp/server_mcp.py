import os
import json
from fastmcp import FastMCP
from wayland_mcp.server.app import capture_screenshot as capture_func, VLMAgent, compare_images as compare_func

# Load API key from mcp.json
try:
    with open('/home/d/Desktop/Rootest/.roo/mcp.json') as f:
        config = json.load(f)
        OPENROUTER_API_KEY = config['mcpServers']['wayland-screenshot']['env']['OPENROUTER_API_KEY']
        print(f"API Key loaded successfully. First 8 chars: {OPENROUTER_API_KEY[:8]}...")
except Exception as e:
    print(f"Error loading API key: {e}")
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

mcp = FastMCP("Wayland MCP")

@mcp.tool()
def capture_screenshot() -> dict:
    import logging
    logging.info("[MCP] capture_screenshot tool called")
    try:
        filename = "screenshot.png"
        result = capture_func(filename)
        if not isinstance(result, dict):
            result = {"success": False, "error": "capture_func did not return a dict"}
        logging.info(f"[MCP] capture_screenshot result: {result}")
        return result
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
    result = vlm_agent.analyze_screenshot(image_path, prompt)
    return result or ""

@mcp.tool()
def execute_action(action: str) -> bool:
    # TODO: Implement action execution logic (key press, click, type)
    return True

if __name__ == "__main__":
    mcp.run()

def main():
    mcp.run()

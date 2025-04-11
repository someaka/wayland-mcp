import os

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
try:
    PORT = int(os.environ.get("WAYLAND_MCP_PORT", "4999"))
except ValueError:
    PORT = 4999

from fastmcp import FastMCP
from wayland_mcp.server.app import capture_screenshot as capture_func, VLMAgent, compare_images as compare_func

mcp = FastMCP("Wayland MCP")

vlm_agent = VLMAgent(OPENROUTER_API_KEY)

@mcp.tool()
def capture_screenshot() -> str:
    filename = "screenshot.png"
    success = capture_func(filename)
    return filename if success else ""

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

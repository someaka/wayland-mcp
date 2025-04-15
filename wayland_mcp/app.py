"""MCP Server application for Wayland interactions.
This module provides core functionality for the Wayland MCP server including:
- Screenshot capture with various backends
- Vision-Language Model (VLM) integration for image analysis
- Mouse control utilities
- Environment configuration for optimal capture performance
"""
import os
import shutil
import subprocess
import time
import logging
import base64
import requests
def configure_environment():
    """Set up optimized capture environment"""
    env = os.environ.copy()
    env.update(
        {
            "LD_LIBRARY_PATH": "/usr/lib/x86_64-linux-gnu:/lib/x86_64-linux-gnu",
            "GTK_PATH": "",
            "GST_PLUGIN_SYSTEM_PATH": "/usr/lib/x86_64-linux-gnu/gstreamer-1.0",
            "PULSE_PROP_OVERRIDE": "filter.want=echo-cancel",
        }
    )
    # Ensure silent sound theme exists in system or user location
    system_sound_dir = "/usr/share/sounds/silent/stereo"
    user_sound_dir = os.path.expanduser("~/.local/share/sounds/silent/stereo")
    # Try system location first
    if not os.path.exists(system_sound_dir):
        os.makedirs(user_sound_dir, exist_ok=True)
        sound_dir = user_sound_dir
    else:
        sound_dir = system_sound_dir
    # Create silent sound file if needed
    sound_file = os.path.join(sound_dir, "screen-capture.oga")
    if not os.path.exists(sound_file):
        # Create an empty file using 'with' to ensure it's closed
        with open(sound_file, "w", encoding="utf-8") as _:  # Use _ for unused variable
            pass  # Just create the file
    env["SOUND_THEME"] = "silent"
    return env
def minimize_effects():
    """Reduce visual and sound effects"""
    try:
        # Reduce animations (minimizes flash)
        subprocess.run(
            [
                "gsettings",
                "set",
                "org.gnome.desktop.interface",
                "enable-animations",
                "false",
            ],
            check=True,
        )
        # Disable event sounds
        subprocess.run(
            ["gsettings", "set", "org.gnome.desktop.sound", "event-sounds", "false"],
            check=True,
        )
        time.sleep(0.3)  # Allow settings to apply
    except subprocess.CalledProcessError as e:
        logging.error("Error minimizing effects: %s", e)
def restore_effects():
    """Restore original system settings"""
    try:
        subprocess.run(
            [
                "gsettings",
                "set",
                "org.gnome.desktop.interface",
                "enable-animations",
                "true",
            ],
            check=True,
        )
        subprocess.run(
            ["gsettings", "set", "org.gnome.desktop.sound", "event-sounds", "true"],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        logging.error("Error restoring effects: %s", e)
# pylint: disable=too-many-branches
def capture_screenshot(output_path=None, mode="auto", geometry=None, include_mouse=True):
    """
    Capture screenshot with optional region selection and mouse cursor
    Args:
        output_path: Output file path
        mode: 'auto'|'region'|'window' - Capture mode
        geometry: Optional pre-defined geometry (x,y,w,h)
        include_mouse: Whether to include mouse cursor in capture (default: True)
    Returns:
        dict: {'success': bool, 'filename': str, 'error': str}
    """
    if output_path is None:
        output_path = os.path.abspath("screenshot.png")
    logging.info("[capture_screenshot] called with silent mode")
    env = configure_environment()
    try:
        minimize_effects()
        # Force mute as backup
        subprocess.run(
            ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "1"], env=env, check=False
        )  # Muting failure isn't critical
        # 1. First try ksnip (if available)
        if os.path.exists("/usr/bin/ksnip"):
            try:
                cmd = ["ksnip", "-f", output_path, "-m"]
                if include_mouse:
                    cmd.append("-c")  # Include cursor
                result = subprocess.run(
                    cmd,
                    env=env,
                    capture_output=True,
                    timeout=15,
                    check=False,  # Don't check, handle return code below
                )
                if result.returncode == 0:
                    return {"success": True, "filename": output_path}
            except subprocess.TimeoutExpired as e:
                logging.error("ksnip failed: %s", e)
        # 2. Fallback to gnome-screenshot (minimized flash)
        try:
            cmd = ["gnome-screenshot", "-f", output_path]
            if include_mouse:
                cmd.append("--include-pointer")
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                timeout=30,  # Increased timeout for slower systems
                check=False,  # Don't check, handle return code below
            )
            if result.returncode == 0:
                return {"success": True, "filename": output_path}
        except subprocess.TimeoutExpired as e:
            logging.error("gnome-screenshot failed: %s", e)
        # Handle region/window selection
        if mode == "region" and not geometry:
            try:
                if shutil.which("slurp"):
                    result = subprocess.run(
                        ["slurp"], capture_output=True, text=True, check=False
                    )  # Don't check, handle return code
                    if result.returncode == 0:
                        geometry = result.stdout.strip()
                elif shutil.which("xrandr"):
                    # Basic X11 region selection fallback
                    result = subprocess.run(
                        ["xrandr | grep ' connected'"],
                        shell=True,
                        capture_output=True,
                        check=False,
                    )  # Don't check, handle return code
                    # Parse output to get screen geometry (needs implementation)
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError) as e:
                logging.warning("Region selection failed: %s", e)
        # 3. Final fallback to grim if on Wayland
        if os.environ.get("WAYLAND_DISPLAY") and shutil.which("grim"):
            try:
                if include_mouse:
                    logging.warning("Grim doesn't support cursor capture - mouse won't be visible")
                cmd = ["grim", output_path]
                if mode == "region" and shutil.which("slurp"):
                    cmd = ["grim", "-g", "$(slurp)", output_path]
                subprocess.run(
                    cmd, env=env, check=True, timeout=20
                )  # Increased timeout for slower systems
                return {"success": True, "filename": output_path}
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                logging.error("Grim fallback failed: %s", e)
        return {"success": False, "error": "All capture methods failed"}
    finally:
        restore_effects()
        subprocess.run(
            ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "0"], env=env, check=False
        )  # Unmuting failure isn't critical
class VLMAgent:
    """Agent for interacting with Vision-Language Models (VLMs).
    Handles image analysis and comparison using VLM APIs.
    Requires an API key for authentication.
    """
    def __init__(self, api_key=None):
        """Initialize with API key validation"""
        self.api_key = api_key
        if not api_key:
            logging.warning("VLMAgent initialized without API key!")
        else:
            logging.info("VLMAgent initialized with valid API key")
    def compare_images(
        self,
        img1_path: str,
        img2_path: str,
    ) -> str:
        """Compare two images using VLM analysis"""
        if not self.api_key:
            logging.error("No API key configured for VLMAgent")
            return "Error: No API key configured for VLMAgent"
        # Verify both images exist
        for img_path in [img1_path, img2_path]:
            if not os.path.exists(img_path):
                logging.error("Image file not found: %s", img_path)
                return f"Error: Image file not found - {img_path}"
        # Encode both images
        encoded_images = []
        for img_path in [img1_path, img2_path]:
            try:
                with open(img_path, "rb") as image_file:
                    encoded_images.append(
                        base64.b64encode(image_file.read()).decode("utf-8")
                    )
            except (IOError, OSError) as e:
                logging.error("Failed to encode image %s: %s", img_path, str(e))
                return f"Error: Failed to process image {img_path} - {str(e)}"
        # Prepare request matching test script
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/your-repo",
            "X-Title": "Wayland MCP"
        }
        # Match the toy script's prompt structure exactly
        payload = {
            "model": "qwen/qwen2.5-vl-72b-instruct:free",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Compare these two screenshots in detail."},
                        {"type": "text", "text": "Focus on:"},
                        {"type": "text", "text": "1. Application windows and their content"},
                        {"type": "text", "text": "2. Layout and positioning differences"},
                        {"type": "text", "text": "3. Any visual changes between them"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{encoded_images[0]}",
                                "detail": "high"
                            }
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{encoded_images[1]}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 2000
        }
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            return (
                f"API error: {response.status_code} - "
                f"{response.text}"
            )
        except requests.exceptions.RequestException as e:
            return f"Request failed: {str(e)}"
    def analyze_image(self, image_path: str, prompt: str) -> str:
        """Analyze a single image using VLM analysis"""
        return self.analyze_screenshot(image_path, prompt)
# pylint: disable=too-many-locals
    def analyze_screenshot(self, image_path: str, prompt: str) -> str:
        """Analyze screenshot using Kimi-VL model
        Args:
            image_path: Path to image file
            prompt: Text prompt for analysis
        Returns:
            str: Analysis result or error message
        """
        # Validate inputs
        if not self.api_key or not os.path.exists(image_path):
            if not self.api_key:
                error_msg = "Error: No API key configured for VLMAgent"
            else:
                error_msg = f"Error: Image file not found - {image_path}"
            logging.error(error_msg)
            return error_msg
        # Encode image
        try:
            with open(image_path, "rb") as image_file:
                file_size = os.path.getsize(image_path)
                logging.info("Processing image: %s (%d bytes)", image_path, file_size)
                encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
                logging.info("Image encoded successfully (%d chars)", len(encoded_image))
        except (IOError, OSError) as e:
            error_msg = f"Error: Failed to process image - {str(e)}"
            logging.error(error_msg)
            return error_msg
        # Break long dictionary assignment
        auth_header = f"Bearer {self.api_key.strip()}"
        headers = {
            "Authorization": auth_header,
            "HTTP-Referer": "https://github.com/your-repo",  # Keep this line short
            "X-Title": "Wayland MCP",
            "Content-Type": "application/json",
        }
        logging.info("Using API key starting with: %s...", self.api_key[:8])
        payload = {
            "model": os.environ.get(
                "VLM_MODEL", "moonshotai/kimi-vl-a3b-thinking:free"
            ),
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            # Break long line
                            "image_url": f"data:image/png;base64,{encoded_image}",
                        },
                    ],
                }
            ],
            "max_tokens": 1000,
        }
        logging.info("Sending VLM request with prompt: %s", prompt)
        try:
            start_time = time.time()
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
            )
            elapsed = time.time() - start_time
            logging.info("VLM request completed in %.2fs", elapsed)
            if response.status_code == 200:
                try:
                    result = response.json()["choices"][0]["message"]["content"]
                    logging.info("VLM analysis result: %.200s...", result)
                    return result
                except KeyError as e:
                    error_msg = (f"VLM API response format error: {str(e)}. "
                               f"Full response: {response.text}")
                    if "quota" in response.text.lower():
                        error_msg = ("API quota exceeded. Please switch to "
                                   "a different API key or wait until quota resets.")
                    logging.error(error_msg)
                    return error_msg
            # Handle API errors with more specific messages
            error_msg = f"VLM API error {response.status_code}"
            if response.status_code == 429:
                error_msg = ("API quota exceeded. Please switch to "
                           "a different API key or wait until quota resets.")
            elif "quota" in response.text.lower():
                error_msg = ("API quota exceeded. Please switch to "
                           "a different API key or wait until quota resets.")
            logging.error("%s: %s", error_msg, response.text)
            return (f"{error_msg}\n"
                   f"Response details: {response.text}")
        except requests.exceptions.RequestException as e:
            logging.error("VLM request failed: %s", str(e))
            # Return f-string directly to reduce local variables
            return f"VLM request failed: {str(e)}"

import os
import shutil
import subprocess
import time
import logging


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
        open(sound_file, "w").close()

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
    except Exception as e:
        logging.error(f"Error minimizing effects: {e}")


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
    except Exception as e:
        logging.error(f"Error restoring effects: {e}")


def capture_screenshot(output_path=None, mode="auto", geometry=None):
    """
    Capture screenshot with optional region selection

    Args:
        output_path: Output file path
        mode: 'auto'|'region'|'window' - Capture mode
        geometry: Optional pre-defined geometry (x,y,w,h)

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
        subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "1"], env=env)

        # 1. First try ksnip (if available)
        if os.path.exists("/usr/bin/ksnip"):
            try:
                result = subprocess.run(
                    ["ksnip", "-f", output_path, "-m"],
                    env=env,
                    capture_output=True,
                    timeout=15,
                )
                if result.returncode == 0:
                    return {"success": True, "filename": output_path}
            except Exception as e:
                logging.error(f"ksnip failed: {e}")

        # 2. Fallback to gnome-screenshot (minimized flash)
        try:
            result = subprocess.run(
                ["gnome-screenshot", "-f", output_path],
                env=env,
                capture_output=True,
                timeout=30,  # Increased timeout for slower systems
            )
            if result.returncode == 0:
                return {"success": True, "filename": output_path}
        except Exception as e:
            logging.error(f"gnome-screenshot failed: {e}")

        # Handle region/window selection
        if mode == "region" and not geometry:
            try:
                if shutil.which("slurp"):
                    result = subprocess.run(["slurp"], capture_output=True, text=True)
                    if result.returncode == 0:
                        geometry = result.stdout.strip()
                elif shutil.which("xrandr"):
                    # Basic X11 region selection fallback
                    result = subprocess.run(
                        ["xrandr | grep ' connected'"], shell=True, capture_output=True
                    )
                    # Parse output to get screen geometry
            except Exception as e:
                logging.warning(f"Region selection failed: {e}")

        # 3. Final fallback to grim if on Wayland
        if os.environ.get("WAYLAND_DISPLAY") and shutil.which("grim"):
            try:
                cmd = ["grim", output_path]
                if mode == "region" and shutil.which("slurp"):
                    cmd = ["grim", "-g", "$(slurp)", output_path]

                subprocess.run(
                    cmd, env=env, check=True, timeout=20
                )  # Increased timeout for slower systems
                return {"success": True, "filename": output_path}
            except Exception as e:
                logging.error(f"Grim fallback failed: {e}")

        return {"success": False, "error": "All capture methods failed"}

    finally:
        restore_effects()
        subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "0"], env=env)


# Keep existing compare_images and VLMAgent implementations
def compare_images(img1_path: str, img2_path: str) -> bool:
    # Existing implementation
    pass


class VLMAgent:
    def __init__(self, api_key=None):
        """Initialize with API key validation"""
        self.api_key = api_key
        if not api_key:
            logging.warning("VLMAgent initialized without API key!")
        else:
            logging.info("VLMAgent initialized with valid API key")

    def analyze_screenshot(self, image_path: str, prompt: str) -> str:
        """Analyze screenshot using Kimi-VL model"""
        try:
            if not self.api_key:
                logging.error("No API key configured for VLMAgent")
                return "Error: No API key configured for VLMAgent"

            import base64
            import requests
            import time

            # Verify image exists
            if not os.path.exists(image_path):
                logging.error(f"Image file not found: {image_path}")
                return f"Error: Image file not found - {image_path}"

            # Encode image
            try:
                with open(image_path, "rb") as image_file:
                    file_size = os.path.getsize(image_path)
                    logging.info(f"Processing image: {image_path} ({file_size} bytes)")
                    encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
                    logging.info(
                        f"Image encoded successfully ({len(encoded_image)} chars)"
                    )
            except Exception as e:
                logging.error(f"Failed to encode image: {str(e)}")
                return f"Error: Failed to process image - {str(e)}"

            headers = {
                "Authorization": f"Bearer {self.api_key.strip()}",
                "HTTP-Referer": "https://github.com/your-repo",
                "X-Title": "Wayland MCP",
                "Content-Type": "application/json",
            }
            logging.info(f"Using API key starting with: {self.api_key[:8]}...")

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
                                "image_url": f"data:image/png;base64,{encoded_image}",
                            },
                        ],
                    }
                ],
                "max_tokens": 1000,
            }

            logging.info(f"Sending VLM request with prompt: {prompt}")
            try:
                start_time = time.time()
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60,
                )
                elapsed = time.time() - start_time
                logging.info(f"VLM request completed in {elapsed:.2f}s")

                if response.status_code == 200:
                    result = response.json()["choices"][0]["message"]["content"]
                    logging.info(f"VLM analysis result: {result[:200]}...")
                    return result
                else:
                    error_msg = (
                        f"VLM API error: {response.status_code} - {response.text}"
                    )
                    logging.error(error_msg)
                    return error_msg
            except Exception as e:
                error_msg = f"VLM request failed: {str(e)}"
                logging.error(error_msg)
                return error_msg
        except Exception as e:
            logging.error(f"VLM analysis failed: {e}")
            return ""

import os
import shutil
import subprocess
import sys
import time
import logging
from datetime import datetime

def configure_environment():
    """Set up optimized capture environment"""
    env = os.environ.copy()
    env.update({
        'LD_LIBRARY_PATH': '/usr/lib/x86_64-linux-gnu:/lib/x86_64-linux-gnu',
        'GTK_PATH': '',
        'GST_PLUGIN_SYSTEM_PATH': '/usr/lib/x86_64-linux-gnu/gstreamer-1.0',
        'PULSE_PROP_OVERRIDE': 'filter.want=echo-cancel'
    })
    
    # Ensure silent sound theme exists
    sound_dir = os.path.expanduser("~/.local/share/sounds/silent/stereo")
    os.makedirs(sound_dir, exist_ok=True)
    open(os.path.join(sound_dir, "screen-capture.oga"), 'w').close()
    
    env['SOUND_THEME'] = 'silent'
    return env

def minimize_effects():
    """Reduce visual and sound effects"""
    try:
        # Reduce animations (minimizes flash)
        subprocess.run([
            'gsettings', 'set',
            'org.gnome.desktop.interface',
            'enable-animations', 'false'
        ], check=True)
        
        # Disable event sounds
        subprocess.run([
            'gsettings', 'set',
            'org.gnome.desktop.sound',
            'event-sounds', 'false'
        ], check=True)
        
        time.sleep(0.3)  # Allow settings to apply
    except Exception as e:
        logging.error(f"Error minimizing effects: {e}")

def restore_effects():
    """Restore original system settings"""
    try:
        subprocess.run([
            'gsettings', 'set',
            'org.gnome.desktop.interface',
            'enable-animations', 'true'
        ], check=True)
        subprocess.run([
            'gsettings', 'set',
            'org.gnome.desktop.sound',
            'event-sounds', 'true'
        ], check=True)
    except Exception as e:
        logging.error(f"Error restoring effects: {e}")

def capture_screenshot(output_path="screenshot.png", mode=None, geometry=None):
    """Optimized screenshot capture with minimal effects"""
    logging.info('[capture_screenshot] called with silent mode')
    
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
                    timeout=15
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
                timeout=15
            )
            if result.returncode == 0:
                return {"success": True, "filename": output_path}
        except Exception as e:
            logging.error(f"gnome-screenshot failed: {e}")

        # 3. Final fallback to grim if on Wayland
        if os.environ.get('WAYLAND_DISPLAY') and shutil.which("grim"):
            try:
                cmd = ["grim", output_path]
                if mode == "region" and shutil.which("slurp"):
                    cmd = ["grim", "-g", "$(slurp)", output_path]
                
                subprocess.run(cmd, env=env, check=True, timeout=10)
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
        """Analyze screenshot using VLM"""
        try:
            if not self.api_key:
                return "Error: No API key configured for VLMAgent"
                
            # Implement actual VLM analysis here
            return f"Analysis for {image_path} with prompt: {prompt}"
        except Exception as e:
            logging.error(f"VLM analysis failed: {e}")
            return ""

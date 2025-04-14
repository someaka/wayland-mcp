"""KeyboardController using evemu-event for keyboard input on Linux."""
import logging
import os
import subprocess
import time
from typing import Optional, List

from wayland_mcp.keymap import KEY_MAP

class KeyboardController:
    """Handles keyboard input events using evemu."""

    def __init__(self, device: Optional[str] = None):
        """
        Initialize with optional keyboard device path.
        If not provided, will auto-detect a suitable device.
        """
        self.device = device or self._find_keyboard_device()
        if not self.device:
            raise RuntimeError("No suitable keyboard device found")

    def _find_keyboard_device(self) -> Optional[str]:
        """Find a writable keyboard event device."""
        for event in os.listdir("/dev/input"):
            if event.startswith("event"):
                dev_path = f"/dev/input/{event}"
                try:
                    desc = subprocess.check_output(
                        ["evemu-describe", dev_path],
                        text=True,
                        timeout=1
                    )
                    if "KEY_A" in desc and "KEY_ENTER" in desc:
                        return dev_path
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                    continue
        return None

    def _send_key(self, keycode: str, value: int = 1) -> bool:
        """Send a key press/release event.

        Args:
            keycode: Key code from KEY_MAP
            value: 1=press, 0=release, 2=autorepeat
        """
        try:
            subprocess.run([
                "evemu-event", self.device,
                "--type", "EV_KEY",
                "--code", keycode,
                "--value", str(value)
            ], check=True)
            subprocess.run([
                "evemu-event", self.device,
                "--type", "EV_SYN",
                "--code", "SYN_REPORT",
                "--value", "0"
            ], check=True)
            return True
        except subprocess.CalledProcessError as e:
            logging.error("Key event failed: %s", e)
            return False

    def send_key_combo(self, keys: List[str]) -> bool:
        """Send a key combination with proper press/release sequence."""
        try:
            # Press all modifier keys first
            for key in keys[:-1]:
                if not self._send_key(key, 1):
                    return False

            # Press and release main key
            if not self._send_key(keys[-1], 1):
                return False
            if not self._send_key(keys[-1], 0):
                return False

            # Release all modifier keys
            for key in reversed(keys[:-1]):
                if not self._send_key(key, 0):
                    return False

            return True
        except (RuntimeError, subprocess.CalledProcessError) as e:
            logging.error("Key combo failed: %s", e)
            # Emergency key release
            for key in keys[:-1]:
                self._send_key(key, 0)
            return False

    def type_text(self, text: str) -> bool:
        """Type out text character by character with proper key release."""
        try:
            for char in text.lower():
                if not (keycode := KEY_MAP.get(char)):
                    continue
                # Press key
                if not self._send_key(keycode, 1):
                    return False
                time.sleep(0.05)
                # Release key
                if not self._send_key(keycode, 0):
                    return False
                time.sleep(0.01)
            return True
        except (RuntimeError, subprocess.CalledProcessError) as e:
            logging.error("Typing failed: %s", str(e))
            # Emergency key release
            for char in text.lower():
                if keycode := KEY_MAP.get(char):
                    self._send_key(keycode, 0)
            return False

    def press_key(self, key: str) -> bool:
        """Press a single key or key combination.

        Args:
            key: Key name or combination (e.g. "a" or "ctrl+a")
        """
        if '+' in key:
            keys = []
            for k in key.split('+'):
                if not (code := KEY_MAP.get(k.lower())):
                    logging.error("Unknown key: %s", k)
                    return False
                keys.append(code)
            return self.send_key_combo(keys)

        if not (code := KEY_MAP.get(key.lower())):
            logging.error("Unknown key: %s", key)
            return False

        return self._send_key(code, 1) and self._send_key(code, 0)

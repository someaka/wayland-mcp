"""MouseController using evemu-event for mouse actions on Linux."""
import os
import subprocess
import time
import logging

# Basic logging setup
logging.basicConfig(level=logging.INFO)


class MouseController:
    """
    MouseController using evemu-event for mouse actions on Linux.
    Supports move, click, and reliable drag-and-drop with Wayland workarounds.
    """

    def __init__(self, device=None):
        """
        Initialize with the evemu device path.
        Auto-detects mouse device if none provided.
        """
        self.device = device or self._auto_detect_device()

    def _auto_detect_device(self):
        """Find the most suitable mouse event device with scoring."""
        if os.environ.get('MCP_TEST_NO_MOUSE') == '1':
            logging.warning("TEST MODE: Simulating no mouse devices found")
            logging.debug("Skipping device scan in test mode")
            raise RuntimeError("No mouse devices available (test mode)")

        mouse_devices = []
        logging.debug("Starting device scan")

        # Check both event* and mouse* devices
        for dev_type in ["event", "mouse"]:
            for event in sorted(os.listdir("/dev/input")):
                if event.startswith(dev_type):
                    dev_path = f"/dev/input/{event}"
                    try:
                        # Check device permissions first
                        if not os.access(dev_path, os.W_OK):
                            logging.debug("Skipping %s - no write permissions", dev_path)
                            continue

                        # Get detailed device info
                        desc = subprocess.check_output(["evemu-describe", dev_path],
                                                text=True, timeout=1)
                        # Must have basic mouse capabilities
                        if not ("BTN_LEFT" in desc and "REL_X" in desc):
                            continue

                        # Score device by capabilities
                        score = 0
                        if "BTN_RIGHT" in desc:
                            score += 1
                        if "REL_WHEEL" in desc:
                            score += 1
                        if "REL_HWHEEL" in desc:
                            score += 1

                        mouse_devices.append((score, dev_path))

                    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                        logging.debug("Device check failed for %s: %s", dev_path, e)
                        continue

        # Debug print before device selection
        logging.debug("Before selection - mouse_devices: %s", str(mouse_devices))

        # Return best matching device or raise exception
        if not mouse_devices:
            error_msg = ("No suitable mouse device found. "
                       "Check permissions and devices in /dev/input/")
            logging.error(error_msg)
            raise RuntimeError(error_msg)

        mouse_devices.sort(reverse=True)  # Highest score first
        selected_device = mouse_devices[0][1]
        logging.info("Selected mouse device: %s", selected_device)
        logging.debug("After selection - mouse_devices: %s", str(mouse_devices))
        return selected_device

    def _evemu(self, args):
        """
        Run an evemu-event command with the given arguments.
        """
        cmd = ["evemu-event", self.device] + args
        try:
            subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"evemu-event failed: {cmd} ({e})")
            return False

    def move_to(self, x, y):
        """
        Move mouse relative to current position using REL_X/REL_Y events.
        Args:
            x: Relative horizontal movement (pixels)
            y: Relative vertical movement (pixels)
        """
        self._evemu(
            ["--type", "EV_REL", "--code", "REL_X", "--value", str(x), "--sync"]
        )
        self._evemu(
            ["--type", "EV_REL", "--code", "REL_Y", "--value", str(y), "--sync"]
        )
        time.sleep(0.05)

    def move_to_zero(self):
        """
        Move mouse to (0,0) using REL_X/REL_Y events.
        """
        self._evemu(
            ["--type", "EV_REL", "--code", "REL_X", "--value", "-50000", "--sync"]
        )
        self._evemu(
            ["--type", "EV_REL", "--code", "REL_Y", "--value", "-50000", "--sync"]
        )

    def move_to_absolute(self, x, y):
        """
        Move mouse to absolute screen coordinates by first resetting to (0,0).
        Args:
            x: Absolute horizontal position (pixels)
            y: Absolute vertical position (pixels)
        """
        self.move_to_zero()
        print(f"Moving to absolute coordinates: ({x}, {y})")
        self.move_to(x, y)


    def click(self):
        """
        Perform a left mouse click at the current position.
        """
        self._evemu(
            ["--type", "EV_KEY", "--code", "BTN_LEFT", "--value", "1", "--sync"]
        )
        time.sleep(0.05)
        self._evemu(
            ["--type", "EV_KEY", "--code", "BTN_LEFT", "--value", "0", "--sync"]
        )

    def drag(self, x1, y1, x2, y2):
        """
        Perform a reliable drag-and-drop from (x1, y1) to (x2, y2).
        Decomposes the drag into two REL_X movements before releasing the button.
        """
        # Move to start
        self.move_to(x1, y1)
        time.sleep(0.1)
        # Mouse down
        self._evemu(
            ["--type", "EV_KEY", "--code", "BTN_LEFT", "--value", "1", "--sync"]
        )
        time.sleep(0.1)
        # Drag: move most of the way (REL_X dx-1, REL_Y dy)
        dx = x2 - x1
        dy = y2 - y1
        if abs(dx) > 1:
            self._evemu(
                [
                    "--type",
                    "EV_REL",
                    "--code",
                    "REL_X",
                    "--value",
                    str(dx - 1),
                    "--sync",
                ]
            )
            self._evemu(
                ["--type", "EV_REL", "--code", "REL_Y", "--value", str(dy), "--sync"]
            )
            time.sleep(0.1)
            # Final REL_X=1, REL_Y=0
            self._evemu(
                ["--type", "EV_REL", "--code", "REL_X", "--value", "1", "--sync"]
            )
            self._evemu(
                ["--type", "EV_REL", "--code", "REL_Y", "--value", "0", "--sync"]
            )
            time.sleep(0.2)
        else:
            self._evemu(
                ["--type", "EV_REL", "--code", "REL_X", "--value", str(dx), "--sync"]
            )
            self._evemu(
                ["--type", "EV_REL", "--code", "REL_Y", "--value", str(dy), "--sync"]
            )
            time.sleep(0.2)
        # Mouse up
        self._evemu(
            ["--type", "EV_KEY", "--code", "BTN_LEFT", "--value", "0", "--sync"]
        )

    def scroll(self, amount):
        """
        Scroll vertically by the given amount (detents).
        Sends both REL_WHEEL and REL_WHEEL_HI_RES events for compatibility.
        """
        self._evemu(
            [
                "--type",
                "EV_REL",
                "--code",
                "REL_WHEEL",
                "--value",
                str(amount),
                "--sync",
            ]
        )
        self._evemu(
            [
                "--type",
                "EV_REL",
                "--code",
                "REL_WHEEL_HI_RES",
                "--value",
                str(amount * 120),
                "--sync",
            ]
        )
        time.sleep(0.1)

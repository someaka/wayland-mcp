import dbus
import os
import logging
from datetime import datetime

def capture_via_portal(output_path):
    """Capture screenshot using XDG Desktop Portal"""
    try:
        logging.info("Attempting XDG Portal screenshot capture")
        bus = dbus.SessionBus()
        portal = bus.get_object('org.freedesktop.portal.Desktop',
                              '/org/freedesktop/portal/desktop')
        screenshot = dbus.Interface(portal, 'org.freedesktop.portal.Screenshot')

        options = {
            'handle_token': 'wayland_mcp',
            'interactive': False
        }

        logging.info("Calling DBus Screenshot method")
        request = screenshot.Screenshot("", options)
        
        default_file = os.path.expanduser(
            f"~/Pictures/Screenshot from {datetime.now().strftime('%Y-%m-%d %H-%M-%S')}.png"
        )
        logging.info(f"Checking for screenshot at: {default_file}")
        
        if os.path.exists(default_file):
            os.rename(default_file, output_path)
            logging.info("Successfully captured screenshot via XDG Portal")
            return True
        else:
            logging.warning("XDG Portal screenshot file not found")
    except Exception as e:
        logging.error(f"Portal screenshot failed: {str(e)}", exc_info=True)
    return False
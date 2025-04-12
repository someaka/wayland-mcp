# Wayland Screenshot Utility

## System Requirements

### Primary Method (Recommended)
1. Ubuntu/Debian Linux with Wayland  
2. gnome-screenshot installed via system package manager (not snap)

### Alternative Method  
1. Python 3.6+  
2. pyautogui installed (`pip install pyautogui`)

## Installation

### For Primary Method:
```bash
# Remove snap version if installed
sudo snap remove gnome-screenshot

# Install system package  
sudo apt install gnome-screenshot

# Make wrapper executable
chmod +x gnome-screenshot-wrapper.sh
```

### For Alternative Method:
```bash
pip install pyautogui
```

## Usage

```bash
python3 wayland_screenshot.py
```

## Troubleshooting

### GLIBC Errors (Primary Method)
1. Verify gnome-screenshot is system-installed  
2. Check wrapper script exists and contains:
```bash
#!/bin/bash
export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:/lib/x86_64-linux-gnu
exec /usr/bin/gnome-screenshot "$@"
```

### PyAutoGUI Issues
1. Ensure all dependencies are installed:
```bash
sudo apt install python3-tk python3-dev
```
2. On Wayland, pyautogui may have limited functionality
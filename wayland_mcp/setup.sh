#!/bin/bash
# Setup script for evemu-event mouse control permissions
# Works immediately without reboot or logout

echo "Setting up evemu-event permissions..."

# 1. Install evemu-event if missing
if ! command -v evemu-event &> /dev/null; then
  echo "Installing evemu-tools (for evemu-event)..."
  sudo apt install -y evemu-tools
fi

# 2. Immediate solution (current session) for evemu-event
echo "Setting setuid bit for evemu-event (current session)..."
if [ -f /usr/bin/evemu-event ]; then
  sudo chmod u+s /usr/bin/evemu-event
fi

# 3. Permanent solution (future sessions) for evemu-event
echo "Configuring sudoers rule for evemu-event..."
echo "$USER ALL=(ALL) NOPASSWD: /usr/bin/evemu-event" | sudo tee /etc/sudoers.d/evemu-event >/dev/null
sudo chmod 440 /etc/sudoers.d/evemu-event

# 4. Verify setup
echo -e "\nVerification:"
ls -la /usr/bin/evemu-event | grep -q 'rws' && echo "evemu-event Setuid OK" || echo "evemu-event Setuid FAILED"
sudo -l | grep -q 'NOPASSWD.*evemu-event' && echo "evemu-event Sudoers OK" || echo "evemu-event Sudoers FAILED"

echo -e "\nSetup complete! You can now use evemu-event without sudo."
echo "Both current and future sessions are configured."
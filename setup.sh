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

# 5. Add user to input group for persistent access
echo "Adding $USER to input group..."
sudo usermod -aG input $USER

# 6. Immediate keyboard device access
echo "Temporarily making input devices writable..."
for dev in /dev/input/event*; do
    sudo chmod 666 $dev 2>/dev/null
done

# 7. Persistent udev rule for keyboard access
echo "Creating udev rule for keyboard access..."
UDEV_RULE="KERNEL==\"event*\", GROUP=\"input\", MODE=\"0666\""
echo $UDEV_RULE | sudo tee /etc/udev/rules.d/99-input.rules >/dev/null
sudo udevadm control --reload-rules
sudo udevadm trigger

echo -e "\nKeyboard setup complete!"
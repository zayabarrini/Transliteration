# Running webApplication (Flask) on the phone 

graph TD
    A[Boot Phone] --> B[Termux: sshd starts automatically]
    C[Ubuntu: mount ~/termux_transliteration] --> D[Edit in VS Code]
    D --> E[Test on phone: python webflask.py]
    E --> F[Unmount when done]

# Ubuntu
termuxmount
termuxunmount
sudo mount -a  # Test mount
cd ~/termux_transliteration && code termux_transliteration/  # Open in VS Code
sshfs -p 8022 -o reconnect,ServerAliveInterval=15 u0_a336@192.168.1.101:/data/data/com.termux/files/home/Transliteration ~/termux_transliteration
mount | grep termux_transliteration # If nothing appears, the mount isn't active

# Phone
sshd  # Start SSH server

In Termux (phone):
cd ~/Transliteration/web
python webflask.py

Auto-restart SSH on phone:
In Termux:

pkg install termux-services
sv-enable sshd


# ~/bin/termux-check

#!/bin/bash
ping -c1 PHONE_IP >/dev/null && echo "Phone reachable" || echo "Phone offline"
mount | grep termux || echo "Mount broken - remount with: sudo mount -a"


# ~/bin/termux-mount
#!/bin/bash
MOUNT_PATH="$HOME/termux_transliteration"
if mountpoint -q "$MOUNT_PATH"; then
    echo "Already mounted"
else
    sudo mount "$MOUNT_PATH" && code "$MOUNT_PATH"
fi

# Unmount Helper (~/bin/termux-unmount):
#!/bin/bash
MOUNT_PATH="$HOME/termux_transliteration"
cd ~  # Ensure we're not in mount
sudo umount -l "$MOUNT_PATH" || sudo umount -f "$MOUNT_PATH"


chmod +x ~/bin/termux-mount
chmod +x ~/bin/termux-unmount
chmod +x ~/bin/termux-check


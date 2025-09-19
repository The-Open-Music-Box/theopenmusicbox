#!/bin/bash

# Setup GPIO libraries for Raspberry Pi
# This script installs the necessary GPIO libraries for physical controls

echo "🔧 Setting up GPIO libraries for Raspberry Pi..."

# Check if running on Raspberry Pi
if ! grep -q "Raspberry" /proc/cpuinfo 2>/dev/null; then
    echo "⚠️  Warning: This doesn't appear to be a Raspberry Pi"
    echo "    Continue anyway? (y/n)"
    read -r response
    if [[ "$response" != "y" ]]; then
        echo "Aborted."
        exit 1
    fi
fi

# Update package list
echo "📦 Updating package list..."
sudo apt-get update

# Install system dependencies
echo "📦 Installing system dependencies..."
sudo apt-get install -y \
    python3-pip \
    python3-dev \
    python3-rpi.gpio \
    python3-gpiozero \
    gcc \
    libc6-dev

# Install Python GPIO libraries
echo "🐍 Installing Python GPIO libraries..."

# Try to install RPi.GPIO (the most compatible)
pip3 install RPi.GPIO || echo "⚠️  RPi.GPIO installation failed, trying alternatives..."

# Install gpiozero (already in requirements but ensure latest)
pip3 install --upgrade gpiozero

# Optional: Install pigpio for more advanced features
echo "📦 Installing optional pigpio..."
sudo apt-get install -y pigpio python3-pigpio
pip3 install pigpio

# Start pigpiod daemon if installed
if command -v pigpiod &> /dev/null; then
    echo "🚀 Starting pigpiod daemon..."
    sudo systemctl enable pigpiod
    sudo systemctl start pigpiod
    echo "✅ pigpiod daemon started"
fi

# Test GPIO access
echo ""
echo "🧪 Testing GPIO access..."
python3 -c "
try:
    import RPi.GPIO as GPIO
    print('✅ RPi.GPIO imported successfully')
    GPIO.setmode(GPIO.BCM)
    GPIO.cleanup()
except Exception as e:
    print(f'⚠️  RPi.GPIO test failed: {e}')

try:
    import gpiozero
    print('✅ gpiozero imported successfully')
except Exception as e:
    print(f'⚠️  gpiozero test failed: {e}')

try:
    import pigpio
    print('✅ pigpio imported successfully')
except Exception as e:
    print(f'⚠️  pigpio test failed: {e}')
"

echo ""
echo "📌 GPIO Pin Configuration for TheOpenMusicBox:"
echo "   - Next Track Button: GPIO 26"
echo "   - Previous Track Button: GPIO 16"
echo "   - Play/Pause Button: GPIO 7"
echo "   - Volume Encoder CLK: GPIO 8"
echo "   - Volume Encoder DT: GPIO 12"
echo ""
echo "✅ GPIO setup complete!"
echo ""
echo "🚀 To test the physical controls:"
echo "   python3 tools/test_physical_controls.py --real-gpio"
echo ""
echo "🎵 To start the application with GPIO:"
echo "   sudo python3 -m uvicorn app.main:app_sio --host 0.0.0.0 --port 5005"
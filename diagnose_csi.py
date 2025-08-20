#!/usr/bin/env python3
"""
CSI Camera Diagnostic Script for Jetson Nano
Comprehensive troubleshooting for CSI camera issues
"""

import subprocess
import os
import time

def run_command(cmd, description=""):
    """Run a command and return output"""
    print(f"\n🔍 {description}")
    print(f"💻 Running: {cmd}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"Error: {result.stderr}")
        return result.returncode == 0, result.stdout
    except subprocess.TimeoutExpired:
        print("❌ Command timed out")
        return False, ""
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False, ""

def check_hardware_detection():
    """Check if CSI camera hardware is detected"""
    print("🔧 HARDWARE DETECTION CHECK")
    print("=" * 50)
    
    # Check video devices
    success, output = run_command("ls -la /dev/video*", "Video devices")
    
    # Check camera in device tree
    run_command("ls /proc/device-tree/ | grep camera", "Camera in device tree")
    
    # Check I2C detection
    run_command("sudo i2cdetect -y -r 6", "I2C bus 6 (common for CSI cameras)")
    run_command("sudo i2cdetect -y -r 7", "I2C bus 7 (alternative CSI bus)")
    
    # Check kernel messages
    run_command("dmesg | grep -i camera | tail -10", "Recent camera kernel messages")
    run_command("dmesg | grep -i csi | tail -10", "Recent CSI kernel messages")
    run_command("dmesg | grep -i tegra | tail -10", "Recent Tegra messages")

def check_nvidia_services():
    """Check NVIDIA Argus and related services"""
    print("\n🛠️ NVIDIA SERVICES CHECK")
    print("=" * 50)
    
    # Check nvargus daemon
    run_command("sudo systemctl status nvargus-daemon", "Argus daemon status")
    
    # Check for argus errors
    run_command("journalctl -u nvargus-daemon --no-pager -n 20", "Recent Argus daemon logs")
    
    # Check NVIDIA processes
    run_command("ps aux | grep nvidia", "NVIDIA processes")

def check_jetpack_version():
    """Check JetPack and L4T version"""
    print("\n📦 JETPACK/L4T VERSION CHECK")
    print("=" * 50)
    
    # Check L4T version
    run_command("cat /etc/nv_tegra_release", "L4T Release version")
    
    # Check JetPack packages
    run_command("dpkg -l | grep nvidia-jetpack", "JetPack packages")
    
    # Check CUDA version
    run_command("nvcc --version", "CUDA version")

def check_gstreamer_support():
    """Check GStreamer and NVIDIA plugins"""
    print("\n🎬 GSTREAMER SUPPORT CHECK")
    print("=" * 50)
    
    # Check GStreamer version
    run_command("gst-launch-1.0 --version", "GStreamer version")
    
    # Check for NVIDIA GStreamer plugins
    run_command("gst-inspect-1.0 nvarguscamerasrc", "nvarguscamerasrc plugin")
    run_command("gst-inspect-1.0 nvvidconv", "nvvidconv plugin")
    
    # List all available plugins
    run_command("gst-inspect-1.0 | grep nv", "Available NVIDIA plugins")

def test_csi_access():
    """Test CSI camera access methods"""
    print("\n📹 CSI CAMERA ACCESS TEST")
    print("=" * 50)
    
    # Test with v4l2-ctl
    run_command("v4l2-ctl --list-devices", "V4L2 devices")
    run_command("v4l2-ctl --device=/dev/video0 --list-formats-ext", "Video0 formats")
    
    # Test simple GStreamer pipeline
    print("\n🧪 Testing basic GStreamer pipeline...")
    test_cmd = (
        "timeout 5s gst-launch-1.0 nvarguscamerasrc sensor-id=0 num-buffers=1 ! "
        "'video/x-raw(memory:NVMM),width=640,height=480' ! nvvidconv ! "
        "'video/x-raw,format=BGR' ! videoconvert ! fakesink -v"
    )
    run_command(test_cmd, "Basic CSI test (5 second timeout)")

def check_permissions():
    """Check camera permissions and groups"""
    print("\n🔐 PERMISSIONS CHECK")
    print("=" * 50)
    
    # Check user groups
    run_command("groups", "Current user groups")
    
    # Check video device permissions
    run_command("ls -la /dev/video*", "Video device permissions")
    
    # Check if user is in video group
    run_command("getent group video", "Video group members")

def suggest_fixes():
    """Suggest potential fixes based on common issues"""
    print("\n💡 COMMON FIXES TO TRY")
    print("=" * 50)
    
    fixes = [
        "1. Restart NVIDIA Argus daemon:",
        "   sudo systemctl restart nvargus-daemon",
        "",
        "2. Add user to video group:",
        "   sudo usermod -a -G video $USER",
        "   (then logout and login again)",
        "",
        "3. Check camera connection:",
        "   - Ensure ribbon cable is firmly connected",
        "   - Try different CSI port (CAM0 vs CAM1)",
        "   - Check for physical damage to cable",
        "",
        "4. Install missing packages:",
        "   sudo apt update",
        "   sudo apt install nvidia-jetpack",
        "   sudo apt install gstreamer1.0-plugins-bad",
        "",
        "5. Camera module specific fixes:",
        "   - For Raspberry Pi Camera v2: Usually works out of box",
        "   - For IMX219: Check if device tree is correct",
        "   - For other modules: May need custom device tree",
        "",
        "6. Force camera detection:",
        "   sudo modprobe nvhost-vi",
        "   sudo modprobe tegra-camera",
        "",
        "7. Check power supply:",
        "   - Ensure adequate power (5V 4A recommended)",
        "   - Some cameras need more power than others"
    ]
    
    for fix in fixes:
        print(fix)

def main():
    """Run comprehensive CSI camera diagnostics"""
    print("🎥 JETSON NANO CSI CAMERA DIAGNOSTIC")
    print("=" * 60)
    print("This script will help diagnose CSI camera issues")
    print("=" * 60)
    
    # Run all diagnostic checks
    check_hardware_detection()
    check_nvidia_services()
    check_jetpack_version()
    check_gstreamer_support()
    test_csi_access()
    check_permissions()
    suggest_fixes()
    
    print("\n✅ DIAGNOSTIC COMPLETE")
    print("=" * 60)
    print("Review the output above to identify potential issues.")
    print("Try the suggested fixes if any problems were found.")

if __name__ == "__main__":
    main()

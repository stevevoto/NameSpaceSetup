
#!/usr/bin/env python3
"""
iperf

Linux Network Namespace Manager with persistent systemd service.

Author: Steve Voto
GitHub: https://github.com/stevevoto/setupNamespace
Version: v1.5
License: MIT

---

Description:

This script manages a persistent Linux network namespace with interface move, 
IP address setup, default route, and systemd service creation.

It is designed to be idempotent — safe to run multiple times — and supports:

- Namespace: ha-test
- Interface: ha-0-0
- IP Address: 2.2.2.3/24
- Gateway: 2.2.2.2
- Internet 8.8.8.8


Features:

- Create namespace and move interface if needed
- Set IP and default route (skip if already exists)
- Install systemd persistent service
- Test with ping (`test`) and iperf (`test2`)
- Easy install: sudo make install

Usage:

    sudo ns-ha-test add
    sudo ns-ha-test force-add
    sudo ns-ha-test update
    sudo ns-ha-test remove
    sudo ns-ha-test status
    sudo ns-ha-test restart
    sudo ns-ha-test reload
    sudo ns-ha-test test
    sudo ns-ha-test test2
    sudo ns-ha-test install

---

Example:

    sudo ns-ha-test add
    sudo ns-ha-test test
    sudo ns-ha-test test2

---

MIT License — Free to use and modify.
"""

"""
setup_namespace.py

Linux Network Namespace Manager with persistent systemd service.

Install:
    sudo python3 setup_namespace.py install

Then use:
    sudo ns-ha-test add
    sudo ns-ha-test test
    sudo ns-ha-test test2
    sudo ns-ha-test status
    sudo ns-ha-test remove

Supports:
    add, force-add, update, remove, status, restart, reload, test, test2, install
"""

import subprocess
import os
import sys

# Configurations
namespace = "ha-test"
interface = "ha-0-0"
ip_address = "2.2.2.3/24"
gateway = "2.2.2.2"

service_file = f"/etc/systemd/system/{namespace}-netns.service"

def run_cmd(cmd, check=True):
    print(f"Running: {cmd}")
    subprocess.run(cmd, shell=True, check=check)

def namespace_exists():
    result = subprocess.run(f"ip netns list | grep -w {namespace}", shell=True, capture_output=True, text=True)
    return result.returncode == 0

def interface_exists():
    if namespace_exists():
        result = subprocess.run(f"ip netns exec {namespace} ip link show {interface}", shell=True, capture_output=True, text=True)
    else:
        result = subprocess.run(f"ip link show {interface}", shell=True, capture_output=True, text=True)
    return result.returncode == 0

def interface_in_namespace():
    result = subprocess.run(f"ip netns exec {namespace} ip link show {interface}", shell=True, capture_output=True, text=True)
    return result.returncode == 0

def ip_address_exists():
    ip_base = ip_address.split("/")[0]
    result = subprocess.run(f"ip netns exec {namespace} ip addr show dev {interface} | grep '{ip_base}'", shell=True, capture_output=True, text=True)
    return result.returncode == 0

def setup_namespace(force=False):
    print(f"\n--- Checking if interface '{interface}' exists ---")
    if not interface_exists():
        print(f"❌ ERROR: Interface '{interface}' not found! Please create the interface first.")
        exit(1)

    print("\n--- Creating Namespace ---")
    if namespace_exists():
        if force:
            print(f"Namespace {namespace} already exists, deleting for force-add...")
            run_cmd(f"ip netns del {namespace}")
            run_cmd(f"ip netns add {namespace}")
        else:
            print(f"Namespace {namespace} already exists, skipping creation.")
    else:
        run_cmd(f"ip netns add {namespace}")

    print("\n--- Moving Interface to Namespace ---")
    if not interface_in_namespace():
        run_cmd(f"ip link set dev {interface} netns {namespace}")
    else:
        print(f"Interface '{interface}' is already inside namespace '{namespace}', skipping move.")

    print("\n--- Bringing Interface Up ---")
    run_cmd(f"ip netns exec {namespace} ip link set {interface} up")
    run_cmd(f"ip netns exec {namespace} ip link set lo up")

    print("\n--- Setting IP Address ---")
    if not ip_address_exists():
        run_cmd(f"ip netns exec {namespace} ip addr add {ip_address} dev {interface}")
    else:
        print(f"IP address {ip_address} already exists on interface '{interface}', skipping.")

    print("\n--- Setting Default Route ---")
    run_cmd(f"ip netns exec {namespace} ip route add default via {gateway}", check=False)

def create_systemd_service():
    print(f"\n--- Creating systemd service: {service_file} ---")
    service_content = f"""[Unit]
Description=Persistent netns setup for {namespace}
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/sbin/ip netns add {namespace}
ExecStartPost=/usr/sbin/ip link set dev {interface} netns {namespace}
ExecStartPost=/usr/sbin/ip netns exec {namespace} ip link set {interface} up
ExecStartPost=/usr/sbin/ip netns exec {namespace} ip link set lo up
ExecStartPost=/usr/sbin/ip netns exec {namespace} ip addr add {ip_address} dev {interface}
ExecStartPost=/usr/sbin/ip netns exec {namespace} ip route add default via {gateway}
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
"""
    with open(service_file, "w") as f:
        f.write(service_content)

    print("\n--- Reloading systemd daemon ---")
    run_cmd("systemctl daemon-reload")

    print(f"\n--- Enabling service: {namespace}-netns.service ---")
    run_cmd(f"systemctl enable {namespace}-netns.service")

def remove_namespace():
    print("\n--- Removing Namespace ---")
    if namespace_exists():
        run_cmd(f"ip netns del {namespace}")
    else:
        print(f"Namespace {namespace} not found, skipping.")

    print("\n--- Disabling systemd service ---")
    run_cmd(f"systemctl disable {namespace}-netns.service || true", check=False)

    if os.path.exists(service_file):
        print(f"\n--- Removing systemd service file: {service_file} ---")
        os.remove(service_file)
        run_cmd("systemctl daemon-reload")
    else:
        print(f"Service file {service_file} not found, skipping.")

def show_status():
    print("\n--- Checking Namespace Status ---")
    if namespace_exists():
        print(f"✅ Namespace '{namespace}' exists.")
    else:
        print(f"❌ Namespace '{namespace}' does not exist.")

    print("\n--- Checking Service Status ---")
    run_cmd(f"systemctl is-enabled {namespace}-netns.service || true", check=False)
    run_cmd(f"systemctl status {namespace}-netns.service || true", check=False)

def restart_all():
    print("\n--- RESTART: Remove + Add Namespace and Service ---")
    remove_namespace()
    setup_namespace(force=False)
    create_systemd_service()
    print("\n✅ Restart complete.")

def reload_service():
    print("\n--- RELOAD: Update service and restart ---")
    create_systemd_service()
    run_cmd(f"systemctl restart {namespace}-netns.service")
    print("\n✅ Reload complete.")

def test_namespace():
    print("\n--- TESTING Namespace (Ping) ---")
    if not namespace_exists():
        print(f"❌ Namespace '{namespace}' does not exist. Please run 'add' first.")
        return

    targets = [gateway, "2.2.2.2", "8.8.8.8", "192.168.7.1"]
    for target in targets:
        print(f"\nPinging {target} inside namespace {namespace}...")
        try:
            run_cmd(f"ip netns exec {namespace} ping -c 4 {target}")
        except subprocess.CalledProcessError:
            print(f"❌ Ping to {target} failed.")

def test_iperf():
    print(f"\n--- TEST2: Verifying iperf connection in namespace {namespace} ---")

    result = subprocess.run("which iperf", shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print("iperf not found.\nPlease install iperf:\n")
        print("Debian/Ubuntu: sudo apt install iperf")
        print("RHEL/CentOS: sudo yum install iperf")
        return

    print("iperf found.\n")
    cmd = f"ip netns exec {namespace} iperf -p 5201 -c 216.218.207.42"
    run_cmd(cmd)

def install_script():
    dest = f"/usr/local/bin/ns-{namespace}"
    print(f"\n--- Installing script to {dest} ---")
    run_cmd(f"cp {sys.argv[0]} {dest}")
    run_cmd(f"chmod +x {dest}")
    print(f"\n✅ Installed as: {dest}")
    print(f"\nUsage:\n  sudo ns-{namespace} add | test | test2 | status | remove | etc.")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("This script must be run as root. Try with sudo.")
        exit(1)

    if len(sys.argv) < 2:
        print(__doc__)
        exit(1)

    action = sys.argv[1].lower()

    if action == "add":
        setup_namespace(force=False)
        create_systemd_service()
        print("\n✅ Namespace added and will persist after reboot.")
    elif action == "force-add":
        setup_namespace(force=True)
        create_systemd_service()
        print("\n✅ Namespace force-added and will persist after reboot.")
    elif action == "update":
        create_systemd_service()
        print("\n✅ Service updated with new settings (namespace unchanged).")
    elif action == "remove":
        remove_namespace()
        print("\n✅ Namespace and service removed.")
    elif action == "status":
        show_status()
    elif action == "restart":
        restart_all()
    elif action == "reload":
        reload_service()
    elif action == "test":
        test_namespace()
    elif action == "test2":
        test_iperf()
    elif action == "install":
        install_script()
    else:
        print(f"\nUnknown action: {action}")
        print(__doc__)
        exit(1)

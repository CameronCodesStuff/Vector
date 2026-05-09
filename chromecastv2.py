#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
[ banner truncated for brevity - same as before ]
"""

import os
import sys
import time
import threading
import logging
import json
import random
import socket
import subprocess
import tempfile
import http.server
import socketserver
import urllib.parse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

# -------------------- DIAGNOSTIC INFO --------------------
print(f"Running with Python: {sys.executable}")
print(f"sys.path: {sys.path}")

# Suppress ALL but critical messages from pychromecast and zeroconf
logging.basicConfig(level=logging.CRITICAL)
logging.getLogger('pychromecast').setLevel(logging.CRITICAL)
logging.getLogger('zeroconf').setLevel(logging.CRITICAL)

# Third-party imports
try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False
    # Dummy classes if colorama not installed
    class Fore:
        RED = ''; GREEN = ''; YELLOW = ''; CYAN = ''; MAGENTA = ''; RESET = ''
    class Back:
        BLACK = ''
    class Style:
        BRIGHT = ''; RESET_ALL = ''

# -------------------- PYCHROMECAST IMPORT WITH VERSION DETECTION --------------------
PYCHROMECAST_AVAILABLE = False
PYCHROMECAST_VERSION = None
HAS_REBOOT = False
HAS_QUEUE_CONTROLS = False
HAS_LAUNCH_APP = False
HAS_ADVANCED_ERRORS = False

try:
    import pychromecast
    PYCHROMECAST_AVAILABLE = True
    try:
        PYCHROMECAST_VERSION = pychromecast.__version__
    except AttributeError:
        PYCHROMECAST_VERSION = "unknown (very old)"
    
    # Detect features
    if hasattr(pychromecast.Chromecast, 'reboot'):
        HAS_REBOOT = True
    
    # Check media controller methods
    try:
        mc = pychromecast.controllers.media.MediaController()
        HAS_QUEUE_CONTROLS = hasattr(mc, 'queue_next') and hasattr(mc, 'queue_prev')
    except:
        pass
    
    if hasattr(pychromecast.Chromecast, 'launch_app'):
        HAS_LAUNCH_APP = True
    
    try:
        from pychromecast.error import ChromecastConnectionError, UnsupportedCommand, LaunchError
        HAS_ADVANCED_ERRORS = True
    except ImportError:
        ChromecastConnectionError = Exception
        UnsupportedCommand = Exception
        LaunchError = Exception
    
    print(f"{Fore.GREEN}[+] pychromecast {PYCHROMECAST_VERSION} loaded{Style.RESET_ALL}")
    if not HAS_REBOOT:
        print(f"{Fore.YELLOW}[!] Reboot not supported in this version{Style.RESET_ALL}")
    if not HAS_QUEUE_CONTROLS:
        print(f"{Fore.YELLOW}[!] Next/previous not supported in this version{Style.RESET_ALL}")
    if not HAS_LAUNCH_APP:
        print(f"{Fore.YELLOW}[!] Launch app not supported in this version{Style.RESET_ALL}")

except ImportError as e:
    print(f"{Fore.RED}[!] Failed to import pychromecast: {e}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Install it: pip install pychromecast{Style.RESET_ALL}")
    sys.exit(1)

# Optional dependencies for advanced features
try:
    import netifaces
    NETIFACES_AVAILABLE = True
except ImportError:
    NETIFACES_AVAILABLE = False

try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False

# -------------------- Configuration --------------------
DEFAULT_TIMEOUT = 5
CONFIG_FILE = "discord_config.json"

# Known app IDs for popular services (used only if HAS_LAUNCH_APP)
APP_IDS = {
    "youtube": "233637DE",
    "netflix": "CA5E8412",
    "spotify": "CC32E753",
    "google_photos": "IHAKAJAKA",
    "plex": "9AC194DC",
}

# Global variables
devices: List[pychromecast.Chromecast] = []
browser = None
zeroconf_instance = None
kick_loop_stop = threading.Event()
scheduler_thread_running = False
scheduler_stop = threading.Event()
monitor_thread_running = False
monitor_stop = threading.Event()
config: Dict[str, Any] = {}  # loaded from CONFIG_FILE
groups: Dict[str, List[str]] = {}  # group name -> list of IPs

# -------------------- Compatibility Helper --------------------
def create_chromecast_from_ip(ip: str, timeout: int = 5) -> Optional[pychromecast.Chromecast]:
    """
    Create a Chromecast object from an IP address.
    Tries modern (host=) and legacy (positional) methods.
    Returns None if connection fails.
    """
    # Modern method (pychromecast >= 4.0.0)
    try:
        cast = pychromecast.Chromecast(host=ip)
        cast.wait(timeout=timeout)
        return cast
    except Exception:
        pass
    
    # Legacy method (older versions)
    try:
        cast = pychromecast.Chromecast(ip)
        cast.wait(timeout=timeout)
        return cast
    except Exception:
        return None

# -------------------- Utility Functions --------------------
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    banner = f"""
{Fore.RED}{Style.BRIGHT}
░█████╗░██╗░░██╗██████╗░░█████╗░███╗░░░███╗███████╗░█████╗░░█████╗░░██████╗████████╗  ██╗░░░██╗██████╗░
██╔══██╗██║░░██║██╔══██╗██╔══██╗████╗░████║██╔════╝██╔══██╗██╔══██╗██╔════╝╚══██╔══╝  ██║░░░██║╚════██╗
██║░░╚═╝███████║██████╔╝██║░░██║██╔████╔██║█████╗░░██║░░╚═╝███████║╚█████╗░░░░██║░░░  ╚██╗░██╔╝░░███╔═╝
██║░░██╗██╔══██║██╔══██╗██║░░██║██║╚██╔╝██║██╔══╝░░██║░░██╗██╔══██║░╚═══██╗░░░██║░░░  ░╚████╔╝░██╔══╝░░
╚█████╔╝██║░░██║██║░░██║╚█████╔╝██║░╚═╝░██║███████╗╚█████╔╝██║░░██║██████╔╝░░░██║░░░  ░░╚██╔╝░░███████╗
░╚════╝░╚═╝░░╚═╝╚═╝░░╚═╝░╚════╝░╚═╝░░░░░╚═╝╚══════╝░╚════╝░╚═╝░░╚═╝╚═════╝░░░░╚═╝░░░  ░░░╚═╝░░░╚══════╝
{Fore.CYAN}═══════════════════════════════════════════════════════
{Fore.MAGENTA}           CameronCodesStuff | Chromecast Killer
{Fore.CYAN}═══════════════════════════════════════════════════════{Style.RESET_ALL}
"""
    print(banner)

def spinner_animation(stop_event, message="Scanning for devices"):
    spinner = ['|', '/', '-', '\\']
    i = 0
    while not stop_event.is_set():
        sys.stdout.write(f"\r{Fore.YELLOW}{message} {spinner[i]}{Style.RESET_ALL}")
        sys.stdout.flush()
        i = (i + 1) % 4
        time.sleep(0.1)
    sys.stdout.write("\r" + " " * 60 + "\r")

def log_message(msg, level="info", end="\n"):
    """Central logging with optional suppression based on anonymity setting."""
    if config.get("settings", {}).get("anonymity", False):
        if level in ("error", "critical"):
            print(msg, end=end)
        return
    print(msg, end=end)

# -------------------- Device Database (Persistent Storage) --------------------
def load_config():
    """Load configuration and device database from JSON file."""
    global config, groups
    default_config = {
        "devices": [],
        "groups": {},
        "settings": {
            "anonymity": False,
            "show_connection_msgs": True,
            "random_jitter": True,
            "jitter_range": [0.5, 1.5],
            "auto_save": True,
            "track_mac": False,
            "monitor_enabled": False,
            "monitor_interval": 60,
        }
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                loaded = json.load(f)
                if "devices" not in loaded:
                    loaded["devices"] = []
                if "groups" not in loaded:
                    loaded["groups"] = {}
                if "settings" not in loaded:
                    loaded["settings"] = default_config["settings"]
                else:
                    for k, v in default_config["settings"].items():
                        if k not in loaded["settings"]:
                            loaded["settings"][k] = v
                config = loaded
                groups = loaded.get("groups", {})
        except Exception as e:
            print(f"{Fore.RED}[-] Failed to load config: {e}{Style.RESET_ALL}")
            config = default_config
            groups = {}
    else:
        config = default_config
        groups = {}

def save_config():
    """Save current configuration and device database to file."""
    try:
        device_list = []
        for dev in devices:
            try:
                ip = dev.cast_info.host
                name = dev.name
                model = dev.model_name
                last_seen = datetime.now().isoformat()
                mac = get_mac_for_ip(ip) if config["settings"].get("track_mac", False) else None
                # Find existing friendly name if any
                friendly = None
                for d in config.get("devices", []):
                    if d.get("ip") == ip:
                        friendly = d.get("friendly_name")
                        break
                device_list.append({
                    "ip": ip,
                    "name": name,
                    "model": model,
                    "last_seen": last_seen,
                    "mac": mac,
                    "friendly_name": friendly
                })
            except:
                pass
        config["devices"] = device_list
        config["groups"] = groups
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        log_message(f"{Fore.GREEN}[+] Configuration saved to {CONFIG_FILE}{Style.RESET_ALL}")
    except Exception as e:
        log_message(f"{Fore.RED}[-] Failed to save config: {e}{Style.RESET_ALL}", level="error")

def load_devices_from_db():
    """Create Chromecast objects from saved device database (using IPs)."""
    global devices
    cleanup_resources()
    loaded = []
    for dev_info in config.get("devices", []):
        ip = dev_info.get("ip")
        if not ip:
            continue
        cast = create_chromecast_from_ip(ip)
        if cast:
            loaded.append(cast)
    devices = loaded
    log_message(f"{Fore.CYAN}[>] Loaded {len(devices)} device(s) from database.{Style.RESET_ALL}")

def get_mac_for_ip(ip):
    """Attempt to get MAC address for given IP using ARP."""
    try:
        if os.name == 'nt':
            output = subprocess.check_output(f"arp -a {ip}", shell=True, text=True)
            lines = output.splitlines()
            for line in lines:
                if ip in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        return parts[1]
        else:
            output = subprocess.check_output(f"arp -n {ip}", shell=True, text=True)
            lines = output.splitlines()
            for line in lines:
                if ip in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        return parts[2]
    except:
        pass
    return None

# -------------------- Group Management --------------------
def create_group(group_name: str):
    """Create a new empty group."""
    if group_name in groups:
        log_message(f"{Fore.YELLOW}[!] Group '{group_name}' already exists{Style.RESET_ALL}")
        return False
    groups[group_name] = []
    log_message(f"{Fore.GREEN}[+] Group '{group_name}' created{Style.RESET_ALL}")
    return True

def delete_group(group_name: str):
    """Delete a group."""
    if group_name not in groups:
        log_message(f"{Fore.YELLOW}[!] Group '{group_name}' does not exist{Style.RESET_ALL}")
        return False
    del groups[group_name]
    log_message(f"{Fore.GREEN}[+] Group '{group_name}' deleted{Style.RESET_ALL}")
    return True

def add_to_group(group_name: str, ip: str):
    """Add a device (by IP) to a group."""
    if group_name not in groups:
        log_message(f"{Fore.YELLOW}[!] Group '{group_name}' does not exist{Style.RESET_ALL}")
        return False
    if ip in groups[group_name]:
        log_message(f"{Fore.YELLOW}[!] {ip} already in group{Style.RESET_ALL}")
        return False
    groups[group_name].append(ip)
    log_message(f"{Fore.GREEN}[+] Added {ip} to '{group_name}'{Style.RESET_ALL}")
    return True

def remove_from_group(group_name: str, ip: str):
    """Remove a device from a group."""
    if group_name not in groups:
        log_message(f"{Fore.YELLOW}[!] Group '{group_name}' does not exist{Style.RESET_ALL}")
        return False
    if ip not in groups[group_name]:
        log_message(f"{Fore.YELLOW}[!] {ip} not in group{Style.RESET_ALL}")
        return False
    groups[group_name].remove(ip)
    log_message(f"{Fore.GREEN}[+] Removed {ip} from '{group_name}'{Style.RESET_ALL}")
    return True

def list_groups():
    """Display all groups and their members."""
    if not groups:
        print(f"{Fore.YELLOW}No groups defined.{Style.RESET_ALL}")
        return
    for gname, members in groups.items():
        print(f"{Fore.CYAN}{gname}:{Style.RESET_ALL}")
        if not members:
            print(f"  {Fore.YELLOW}(empty){Style.RESET_ALL}")
        else:
            for ip in members:
                # Try to get friendly name
                friendly = None
                for d in config.get("devices", []):
                    if d.get("ip") == ip:
                        friendly = d.get("friendly_name") or d.get("name")
                        break
                display = friendly if friendly else ip
                print(f"  {Fore.GREEN}{display}{Style.RESET_ALL} ({ip})")

def kick_group(group_name: str):
    """Kick all devices in a group."""
    if group_name not in groups:
        log_message(f"{Fore.YELLOW}[!] Group '{group_name}' does not exist{Style.RESET_ALL}")
        return
    ips = groups[group_name]
    if not ips:
        log_message(f"{Fore.YELLOW}[!] Group '{group_name}' is empty{Style.RESET_ALL}")
        return
    log_message(f"{Fore.CYAN}[>] Kicking group '{group_name}' ({len(ips)} devices){Style.RESET_ALL}")
    for ip in ips:
        cast = create_chromecast_from_ip(ip, timeout=3)
        if cast:
            try:
                cast.quit_app()
                log_message(f"{Fore.GREEN}[+] Kicked {ip}{Style.RESET_ALL}")
                cast.disconnect()
            except Exception as e:
                log_message(f"{Fore.RED}[-] Failed to kick {ip}: {e}{Style.RESET_ALL}", level="error")
        else:
            log_message(f"{Fore.RED}[-] Could not connect to {ip}{Style.RESET_ALL}", level="error")

# -------------------- Status Monitoring --------------------
def monitor_loop():
    """Background thread that periodically checks device availability."""
    global monitor_thread_running
    interval = config["settings"].get("monitor_interval", 60)
    log_message(f"{Fore.CYAN}[>] Status monitor started (interval {interval}s){Style.RESET_ALL}")
    while not monitor_stop.is_set():
        for dev_info in config.get("devices", []):
            ip = dev_info.get("ip")
            if not ip:
                continue
            cast = create_chromecast_from_ip(ip, timeout=2)
            if cast:
                dev_info["last_seen"] = datetime.now().isoformat()
                cast.disconnect()
        monitor_stop.wait(interval)
    monitor_thread_running = False
    log_message(f"{Fore.YELLOW}[!] Status monitor stopped{Style.RESET_ALL}")

def start_monitor():
    global monitor_thread_running, monitor_stop
    if monitor_thread_running:
        log_message(f"{Fore.YELLOW}[!] Monitor already running{Style.RESET_ALL}")
        return
    monitor_stop.clear()
    t = threading.Thread(target=monitor_loop)
    t.daemon = True
    t.start()
    monitor_thread_running = True

def stop_monitor():
    global monitor_thread_running
    if not monitor_thread_running:
        return
    monitor_stop.set()
    for _ in range(10):
        if not monitor_thread_running:
            break
        time.sleep(0.2)

# -------------------- Export/Import --------------------
def export_devices(filename: str):
    """Export device list to a JSON file."""
    try:
        with open(filename, 'w') as f:
            json.dump(config.get("devices", []), f, indent=2)
        log_message(f"{Fore.GREEN}[+] Exported {len(config.get('devices', []))} devices to {filename}{Style.RESET_ALL}")
    except Exception as e:
        log_message(f"{Fore.RED}[-] Export failed: {e}{Style.RESET_ALL}", level="error")

def import_devices(filename: str):
    """Import device list from a JSON file and merge with existing."""
    try:
        with open(filename, 'r') as f:
            imported = json.load(f)
        if not isinstance(imported, list):
            log_message(f"{Fore.RED}[-] Invalid format: expected list{Style.RESET_ALL}", level="error")
            return
        existing_ips = {d.get("ip") for d in config.get("devices", []) if d.get("ip")}
        new_count = 0
        for dev in imported:
            if dev.get("ip") not in existing_ips:
                config["devices"].append(dev)
                new_count += 1
        log_message(f"{Fore.GREEN}[+] Imported {new_count} new devices from {filename}{Style.RESET_ALL}")
        if config["settings"].get("auto_save", True):
            save_config()
    except Exception as e:
        log_message(f"{Fore.RED}[-] Import failed: {e}{Style.RESET_ALL}", level="error")

# -------------------- Device Actions --------------------
def set_volume(devices_list: List[pychromecast.Chromecast], volume: int):
    """Set volume to absolute value (0-100)."""
    for dev in devices_list:
        try:
            dev.set_volume(volume/100.0)
            log_message(f"{Fore.GREEN}[+] {dev.name} volume set to {volume}%{Style.RESET_ALL}")
        except Exception as e:
            log_message(f"{Fore.RED}[-] {dev.name}: {e}{Style.RESET_ALL}", level="error")

def volume_up(devices_list: List[pychromecast.Chromecast], delta: int = 10):
    """Increase volume by delta percentage points."""
    for dev in devices_list:
        try:
            current = dev.status.volume_level * 100
            new_vol = min(100, current + delta)
            dev.set_volume(new_vol/100.0)
            log_message(f"{Fore.GREEN}[+] {dev.name} volume increased to {new_vol}%{Style.RESET_ALL}")
        except Exception as e:
            log_message(f"{Fore.RED}[-] {dev.name}: {e}{Style.RESET_ALL}", level="error")

def volume_down(devices_list: List[pychromecast.Chromecast], delta: int = 10):
    """Decrease volume by delta percentage points."""
    for dev in devices_list:
        try:
            current = dev.status.volume_level * 100
            new_vol = max(0, current - delta)
            dev.set_volume(new_vol/100.0)
            log_message(f"{Fore.GREEN}[+] {dev.name} volume decreased to {new_vol}%{Style.RESET_ALL}")
        except Exception as e:
            log_message(f"{Fore.RED}[-] {dev.name}: {e}{Style.RESET_ALL}", level="error")

def mute(devices_list: List[pychromecast.Chromecast], mute_state: bool = True):
    """Mute or unmute devices."""
    for dev in devices_list:
        try:
            dev.set_volume_muted(mute_state)
            state = "muted" if mute_state else "unmuted"
            log_message(f"{Fore.GREEN}[+] {dev.name} {state}{Style.RESET_ALL}")
        except Exception as e:
            log_message(f"{Fore.RED}[-] {dev.name}: {e}{Style.RESET_ALL}", level="error")

def playback_control(devices_list: List[pychromecast.Chromecast], action: str, **kwargs):
    """Control playback: play, pause, stop, next, previous, seek."""
    for dev in devices_list:
        mc = dev.media_controller
        try:
            if action == "play":
                mc.play()
            elif action == "pause":
                mc.pause()
            elif action == "stop":
                mc.stop()
            elif action == "next":
                if HAS_QUEUE_CONTROLS:
                    mc.queue_next()
                else:
                    log_message(f"{Fore.YELLOW}[!] Next not supported in this version{Style.RESET_ALL}")
            elif action == "previous":
                if HAS_QUEUE_CONTROLS:
                    mc.queue_prev()
                else:
                    log_message(f"{Fore.YELLOW}[!] Previous not supported{Style.RESET_ALL}")
            elif action == "seek":
                seconds = kwargs.get("seconds", 30)
                if hasattr(mc, 'seek'):
                    mc.seek(seconds)
                else:
                    log_message(f"{Fore.YELLOW}[!] Seek not supported{Style.RESET_ALL}")
            log_message(f"{Fore.GREEN}[+] {dev.name}: {action}{Style.RESET_ALL}")
        except Exception as e:
            log_message(f"{Fore.RED}[-] {dev.name}: {e}{Style.RESET_ALL}", level="error")

def reboot_device(devices_list: List[pychromecast.Chromecast]):
    """Reboot the Chromecast (if supported)."""
    if not HAS_REBOOT:
        log_message(f"{Fore.YELLOW}[!] Reboot not supported in this version{Style.RESET_ALL}")
        return
    for dev in devices_list:
        try:
            dev.reboot()
            log_message(f"{Fore.GREEN}[+] {dev.name} reboot initiated{Style.RESET_ALL}")
        except Exception as e:
            log_message(f"{Fore.RED}[-] {dev.name}: {e}{Style.RESET_ALL}", level="error")

def launch_app(devices_list: List[pychromecast.Chromecast], app_name: str, content_id: str = None):
    """Launch a known app by name or custom app ID (if supported)."""
    if not HAS_LAUNCH_APP:
        log_message(f"{Fore.YELLOW}[!] Launch app not supported in this version{Style.RESET_ALL}")
        return
    app_id = APP_IDS.get(app_name.lower(), app_name)
    for dev in devices_list:
        try:
            if content_id:
                dev.launch_app(app_id, content_id)
            else:
                dev.launch_app(app_id)
            log_message(f"{Fore.GREEN}[+] {dev.name} launched {app_name}{Style.RESET_ALL}")
        except Exception as e:
            log_message(f"{Fore.RED}[-] {dev.name}: {e}{Style.RESET_ALL}", level="error")

def quit_app(devices_list: List[pychromecast.Chromecast]):
    """Quit the current app."""
    for dev in devices_list:
        try:
            dev.quit_app()
            log_message(f"{Fore.GREEN}[+] {dev.name} quit current app{Style.RESET_ALL}")
        except Exception as e:
            log_message(f"{Fore.RED}[-] {dev.name}: {e}{Style.RESET_ALL}", level="error")

def list_running_apps(devices_list: List[pychromecast.Chromecast]):
    """Display running apps on each device."""
    for dev in devices_list:
        try:
            app_id = dev.app_id
            app_name = dev.app_display_name
            if app_id:
                log_message(f"{Fore.CYAN}{dev.name}: {app_name} ({app_id}){Style.RESET_ALL}")
            else:
                log_message(f"{Fore.YELLOW}{dev.name}: No app running{Style.RESET_ALL}")
        except Exception as e:
            log_message(f"{Fore.RED}[-] {dev.name}: {e}{Style.RESET_ALL}", level="error")

def cast_media(devices_list: List[pychromecast.Chromecast], media_url: str, content_type: str = "video/mp4", title: str = None):
    """Cast media from a URL."""
    for dev in devices_list:
        try:
            mc = dev.media_controller
            mc.play_media(media_url, content_type, title=title)
            mc.block_until_active()
            log_message(f"{Fore.GREEN}[+] {dev.name} now casting{Style.RESET_ALL}")
        except Exception as e:
            log_message(f"{Fore.RED}[-] {dev.name}: {e}{Style.RESET_ALL}", level="error")

def cast_local_file(devices_list: List[pychromecast.Chromecast], file_path: str):
    """Serve a local file via temporary HTTP server and cast it."""
    if not os.path.isfile(file_path):
        log_message(f"{Fore.RED}[-] File not found: {file_path}{Style.RESET_ALL}", level="error")
        return
    ext = os.path.splitext(file_path)[1].lower()
    content_type = {
        '.mp4': 'video/mp4',
        '.mkv': 'video/x-matroska',
        '.avi': 'video/x-msvideo',
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/wav',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
    }.get(ext, 'video/mp4')

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = '127.0.0.1'
    finally:
        s.close()

    port = random.randint(8000, 9000)
    handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", port), handler)
    thread = threading.Thread(target=httpd.serve_forever)
    thread.daemon = True
    thread.start()

    os.chdir(os.path.dirname(file_path))
    filename = os.path.basename(file_path)
    url = f"http://{local_ip}:{port}/{filename}"
    log_message(f"{Fore.CYAN}[>] Serving {filename} at {url}{Style.RESET_ALL}")
    cast_media(devices_list, url, content_type, title=filename)
    log_message(f"{Fore.YELLOW}[!] Press Enter to stop server when done...{Style.RESET_ALL}")
    input()
    httpd.shutdown()
    thread.join()

# -------------------- Bulk Operations --------------------
def select_multiple_devices(prompt: str = "Select devices (comma-separated numbers or A for all): ") -> List[pychromecast.Chromecast]:
    """Interactive selection of multiple devices from the global list."""
    if not devices:
        log_message(f"{Fore.RED}[!] No devices.{Style.RESET_ALL}", level="error")
        return []
    print(f"{Fore.CYAN}Available devices:{Style.RESET_ALL}")
    for idx, dev in enumerate(devices, 1):
        try:
            host = dev.cast_info.host
        except:
            host = "Unknown"
        print(f"  {Fore.RED}[{idx}]{Style.RESET_ALL} {Fore.GREEN}{dev.name}{Style.RESET_ALL} ({host})")
    print(f"  {Fore.RED}[A]{Style.RESET_ALL} {Fore.GREEN}ALL devices{Style.RESET_ALL}")
    choice = input(f"{Fore.YELLOW}{prompt}{Style.RESET_ALL}").strip()
    targets = []
    if choice.upper() == 'A':
        targets = devices[:]
    else:
        parts = choice.split(',')
        for p in parts:
            p = p.strip()
            if p.isdigit():
                idx = int(p)
                if 1 <= idx <= len(devices):
                    targets.append(devices[idx-1])
                else:
                    log_message(f"{Fore.RED}Invalid index: {idx}{Style.RESET_ALL}", level="error")
            else:
                log_message(f"{Fore.RED}Invalid input: {p}{Style.RESET_ALL}", level="error")
    return targets

# -------------------- Scheduled Actions --------------------
scheduled_jobs = []

def schedule_action(action_func, args, run_time):
    """Schedule a one-time action at a specific time."""
    delay = (run_time - datetime.now()).total_seconds()
    if delay < 0:
        log_message(f"{Fore.RED}[-] Time must be in the future{Style.RESET_ALL}", level="error")
        return
    def job():
        time.sleep(delay)
        action_func(*args)
    t = threading.Thread(target=job)
    t.daemon = True
    t.start()
    scheduled_jobs.append(t)
    log_message(f"{Fore.GREEN}[+] Action scheduled at {run_time.strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")

def schedule_recurring(action_func, args, interval_seconds):
    """Schedule a recurring action using schedule library if available."""
    if SCHEDULE_AVAILABLE:
        schedule.every(interval_seconds).seconds.do(lambda: action_func(*args))
        log_message(f"{Fore.GREEN}[+] Recurring action scheduled every {interval_seconds}s{Style.RESET_ALL}")
    else:
        def loop():
            while not scheduler_stop.is_set():
                action_func(*args)
                scheduler_stop.wait(interval_seconds)
        t = threading.Thread(target=loop)
        t.daemon = True
        t.start()
        scheduled_jobs.append(t)
        log_message(f"{Fore.GREEN}[+] Recurring action started (simple thread){Style.RESET_ALL}")

def run_scheduler():
    """Background thread to run schedule library."""
    global scheduler_thread_running
    scheduler_thread_running = True
    while not scheduler_stop.is_set():
        schedule.run_pending()
        time.sleep(1)
    scheduler_thread_running = False

def stop_scheduler():
    scheduler_stop.set()
    for t in scheduled_jobs:
        t.join(timeout=1)

# -------------------- Kick from saved devices (cross-network) --------------------
def kick_from_saved_menu():
    """Load saved IPs from config and kick them directly without scanning or connecting."""
    clear_screen()
    print_banner()
    saved_devs = config.get("devices", [])
    if not saved_devs:
        print(f"{Fore.YELLOW}[!] No saved devices in database.{Style.RESET_ALL}")
        input(f"{Fore.YELLOW}Press Enter...{Style.RESET_ALL}")
        return

    print(f"{Fore.CYAN}[>] Loading {len(saved_devs)} saved device(s) and kicking...{Style.RESET_ALL}\n")
    successful = 0
    failed = []
    for dev_info in saved_devs:
        ip = dev_info.get("ip")
        friendly = dev_info.get("friendly_name") or dev_info.get("name") or ip
        if not ip:
            continue
        print(f"{Fore.YELLOW}-> Attempting to kick {friendly} ({ip})...{Style.RESET_ALL}")
        cast = create_chromecast_from_ip(ip, timeout=5)
        if cast:
            try:
                cast.quit_app()
                print(f"{Fore.GREEN}  [+] Successfully kicked{Style.RESET_ALL}")
                successful += 1
                cast.disconnect()
            except Exception as e:
                print(f"{Fore.RED}  [-] Failed: {e}{Style.RESET_ALL}")
                failed.append(ip)
        else:
            print(f"{Fore.RED}  [-] Could not connect{Style.RESET_ALL}")
            failed.append(ip)

    print(f"\n{Fore.CYAN}[>] Kicked {successful} of {len(saved_devs)} devices.{Style.RESET_ALL}")
    if failed:
        print(f"{Fore.YELLOW}Failed IPs: {', '.join(failed)}{Style.RESET_ALL}")
    input(f"{Fore.YELLOW}Press Enter...{Style.RESET_ALL}")

# -------------------- Cleanup --------------------
def cleanup_resources():
    """Gracefully shut down all devices and the browser, allowing threads to exit."""
    global devices, browser, zeroconf_instance
    for dev in devices:
        try:
            dev.disconnect()
        except:
            pass
    time.sleep(1)
    if browser:
        try:
            browser.stop_discovery()
        except:
            pass
        browser = None
    if zeroconf_instance:
        try:
            zeroconf_instance.close()
        except:
            pass
        zeroconf_instance = None
    devices = []

# -------------------- Menu Functions --------------------
def scan_menu():
    """Scan and display devices."""
    clear_screen()
    print_banner()
    print(f"{Fore.CYAN}[>] Scanning network for Chromecast devices...{Style.RESET_ALL}")
    refresh_devices()
    if not devices:
        print(f"{Fore.RED}[-] No Chromecast devices found.{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.GREEN}[+] Found {len(devices)} device(s):{Style.RESET_ALL}\n")
        for idx, dev in enumerate(devices, 1):
            print_device_info(dev, detailed=False, index=idx)
    if config["settings"].get("auto_save", True):
        save_config()
    input(f"\n{Fore.YELLOW}Press Enter to return to main menu...{Style.RESET_ALL}")

def ip_range_scan_menu():
    """Manual IP range scan."""
    clear_screen()
    print_banner()
    network = input(f"{Fore.CYAN}Enter network in CIDR notation (e.g., 192.168.1.0/24): {Style.RESET_ALL}").strip()
    if not network:
        return
    new_devs = ip_range_scan(network)
    if new_devs:
        global devices
        devices.extend(new_devs)
        print(f"{Fore.GREEN}[+] Added {len(new_devs)} device(s) from scan.{Style.RESET_ALL}")
        if config["settings"].get("auto_save", True):
            save_config()
    else:
        print(f"{Fore.YELLOW}[-] No Chromecasts found in range.{Style.RESET_ALL}")
    input(f"{Fore.YELLOW}Press Enter...{Style.RESET_ALL}")

def list_detailed_menu():
    """Show detailed info of all devices."""
    clear_screen()
    print_banner()
    if not devices:
        print(f"{Fore.YELLOW}[!] No devices in list. Run scan first.{Style.RESET_ALL}")
    else:
        print(f"{Fore.CYAN}[>] Detailed device list:{Style.RESET_ALL}\n")
        for idx, dev in enumerate(devices, 1):
            print_device_info(dev, detailed=True, index=idx)
    input(f"\n{Fore.YELLOW}Press Enter to return...{Style.RESET_ALL}")

def print_device_info(device, detailed=False, index=None):
    """Pretty print device info."""
    prefix = f"{Fore.RED}[{index}]{Style.RESET_ALL} " if index is not None else ""
    name_color = Fore.GREEN
    ip_color = Fore.CYAN
    model_color = Fore.YELLOW
    media_color = Fore.MAGENTA

    try:
        host = device.cast_info.host
    except AttributeError:
        host = "Unknown"

    print(f"{prefix}{name_color}{device.name}{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}IP:{Style.RESET_ALL} {ip_color}{host}{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}Model:{Style.RESET_ALL} {model_color}{device.model_name}{Style.RESET_ALL}")
    if detailed:
        if device.status:
            vol = device.status.volume_level * 100 if device.status.volume_level else 0
            muted = device.status.volume_muted
            print(f"  {Fore.YELLOW}Volume:{Style.RESET_ALL} {Fore.CYAN}{vol:.0f}%{Style.RESET_ALL} {'(Muted)' if muted else ''}")
        if device.media_controller.status:
            mc = device.media_controller.status
            if mc.title:
                print(f"  {Fore.YELLOW}Now playing:{Style.RESET_ALL}")
                if mc.title:
                    print(f"    {media_color}Title: {mc.title}{Style.RESET_ALL}")
                if mc.artist:
                    print(f"    {media_color}Artist: {mc.artist}{Style.RESET_ALL}")
                if mc.album_name:
                    print(f"    {media_color}Album: {mc.album_name}{Style.RESET_ALL}")
                if mc.player_state:
                    print(f"    {media_color}State: {mc.player_state}{Style.RESET_ALL}")

def kick_devices(targets):
    """Kick the given list of devices (stop casting)."""
    for dev in targets:
        try:
            host = dev.cast_info.host
        except:
            host = "Unknown"
        log_message(f"{Fore.YELLOW}-> Stopping casting on {Fore.GREEN}{dev.name}{Fore.YELLOW} ({host})...{Style.RESET_ALL}")
        try:
            dev.quit_app()
            log_message(f"{Fore.GREEN}  [+] Successfully stopped.{Style.RESET_ALL}")
        except Exception as e:
            log_message(f"{Fore.RED}  [-] Failed: {e}{Style.RESET_ALL}", level="error")

def kick_menu():
    """Stop casting on selected device(s)."""
    clear_screen()
    print_banner()
    targets = select_multiple_devices()
    if not targets:
        return
    kick_devices(targets)
    input(f"\n{Fore.YELLOW}Press Enter to return...{Style.RESET_ALL}")

def continuous_kick_loop(interval):
    """Run kick on all devices every `interval` seconds until stop event is set."""
    global kick_loop_stop
    kick_loop_stop.clear()
    log_message(f"{Fore.CYAN}[>] Continuous kick loop started. Interval: {interval}s. Press Enter to stop.{Style.RESET_ALL}\n")
    jitter = config["settings"].get("random_jitter", False)
    jitter_range = config["settings"].get("jitter_range", [0.5, 1.5])
    while not kick_loop_stop.is_set():
        if devices:
            log_message(f"{Fore.MAGENTA}[{datetime.now().strftime('%H:%M:%S')}] Kicking all devices...{Style.RESET_ALL}")
            kick_devices(devices)
        else:
            log_message(f"{Fore.YELLOW}[!] No devices in list. Scan first.{Style.RESET_ALL}")
        sleep_time = interval
        if jitter:
            sleep_time *= random.uniform(jitter_range[0], jitter_range[1])
        kick_loop_stop.wait(sleep_time)

def continuous_kick_menu():
    """Menu for continuous kick loop."""
    global kick_loop_stop
    clear_screen()
    print_banner()
    if not devices:
        print(f"{Fore.RED}[!] No devices. Run scan first.{Style.RESET_ALL}")
        input(f"{Fore.YELLOW}Press Enter...{Style.RESET_ALL}")
        return

    try:
        interval = float(input(f"{Fore.CYAN}Enter base interval in seconds (e.g., 10): {Style.RESET_ALL}").strip())
        if interval <= 0:
            raise ValueError
    except ValueError:
        print(f"{Fore.RED}[!] Invalid interval.{Style.RESET_ALL}")
        input(f"{Fore.YELLOW}Press Enter...{Style.RESET_ALL}")
        return

    loop_thread = threading.Thread(target=continuous_kick_loop, args=(interval,))
    loop_thread.daemon = True
    loop_thread.start()

    input(f"{Fore.YELLOW}Press Enter to stop the continuous kick loop...{Style.RESET_ALL}")
    kick_loop_stop.set()
    loop_thread.join(timeout=interval+1)
    print(f"{Fore.GREEN}Continuous kick loop stopped.{Style.RESET_ALL}")
    time.sleep(1)

def connect_menu():
    """Connect to selected device(s) and show status."""
    clear_screen()
    print_banner()
    targets = select_multiple_devices()
    if not targets:
        return
    for dev in targets:
        try:
            host = dev.cast_info.host
        except:
            host = "Unknown"
        log_message(f"\n{Fore.CYAN}[>] Connecting to {Fore.GREEN}{dev.name}{Fore.CYAN} ({host})...{Style.RESET_ALL}")
        print_device_info(dev, detailed=True)
    input(f"\n{Fore.YELLOW}Press Enter to return...{Style.RESET_ALL}")

def volume_menu():
    """Volume control submenu."""
    while True:
        clear_screen()
        print_banner()
        print(f"{Fore.CYAN}=== Volume Control ==={Style.RESET_ALL}\n")
        print(f"{Fore.RED}[1]{Fore.YELLOW} Set volume (0-100)")
        print(f"{Fore.RED}[2]{Fore.YELLOW} Volume up (+10)")
        print(f"{Fore.RED}[3]{Fore.YELLOW} Volume down (-10)")
        print(f"{Fore.RED}[4]{Fore.YELLOW} Mute")
        print(f"{Fore.RED}[5]{Fore.YELLOW} Unmute")
        print(f"{Fore.RED}[6]{Fore.YELLOW} Back")
        choice = input(f"{Fore.GREEN}Select: {Style.RESET_ALL}").strip()
        if choice == '6':
            break
        targets = select_multiple_devices()
        if not targets:
            continue
        if choice == '1':
            try:
                vol = int(input(f"{Fore.CYAN}Volume (0-100): {Style.RESET_ALL}").strip())
                if 0 <= vol <= 100:
                    set_volume(targets, vol)
                else:
                    print(f"{Fore.RED}Invalid volume{Style.RESET_ALL}")
            except:
                print(f"{Fore.RED}Invalid input{Style.RESET_ALL}")
        elif choice == '2':
            volume_up(targets)
        elif choice == '3':
            volume_down(targets)
        elif choice == '4':
            mute(targets, True)
        elif choice == '5':
            mute(targets, False)
        input(f"{Fore.YELLOW}Press Enter...{Style.RESET_ALL}")

def playback_menu():
    """Playback control submenu."""
    while True:
        clear_screen()
        print_banner()
        print(f"{Fore.CYAN}=== Playback Control ==={Style.RESET_ALL}\n")
        print(f"{Fore.RED}[1]{Fore.YELLOW} Play")
        print(f"{Fore.RED}[2]{Fore.YELLOW} Pause")
        print(f"{Fore.RED}[3]{Fore.YELLOW} Stop")
        print(f"{Fore.RED}[4]{Fore.YELLOW} Next")
        print(f"{Fore.RED}[5]{Fore.YELLOW} Previous")
        print(f"{Fore.RED}[6]{Fore.YELLOW} Seek")
        print(f"{Fore.RED}[7]{Fore.YELLOW} Back")
        choice = input(f"{Fore.GREEN}Select: {Style.RESET_ALL}").strip()
        if choice == '7':
            break
        targets = select_multiple_devices()
        if not targets:
            continue
        if choice == '1':
            playback_control(targets, "play")
        elif choice == '2':
            playback_control(targets, "pause")
        elif choice == '3':
            playback_control(targets, "stop")
        elif choice == '4':
            playback_control(targets, "next")
        elif choice == '5':
            playback_control(targets, "previous")
        elif choice == '6':
            try:
                sec = int(input(f"{Fore.CYAN}Seek to (seconds): {Style.RESET_ALL}").strip())
                playback_control(targets, "seek", seconds=sec)
            except:
                print(f"{Fore.RED}Invalid input{Style.RESET_ALL}")
        input(f"{Fore.YELLOW}Press Enter...{Style.RESET_ALL}")

def app_menu():
    """Application management submenu."""
    while True:
        clear_screen()
        print_banner()
        print(f"{Fore.CYAN}=== Application Management ==={Style.RESET_ALL}\n")
        print(f"{Fore.RED}[1]{Fore.YELLOW} List running apps")
        print(f"{Fore.RED}[2]{Fore.YELLOW} Launch YouTube")
        print(f"{Fore.RED}[3]{Fore.YELLOW} Launch Netflix")
        print(f"{Fore.RED}[4]{Fore.YELLOW} Launch Spotify")
        print(f"{Fore.RED}[5]{Fore.YELLOW} Launch custom app ID")
        print(f"{Fore.RED}[6]{Fore.YELLOW} Quit current app")
        print(f"{Fore.RED}[7]{Fore.YELLOW} Back")
        choice = input(f"{Fore.GREEN}Select: {Style.RESET_ALL}").strip()
        if choice == '7':
            break
        targets = select_multiple_devices()
        if not targets:
            continue
        if choice == '1':
            list_running_apps(targets)
        elif choice == '2':
            launch_app(targets, "youtube")
        elif choice == '3':
            launch_app(targets, "netflix")
        elif choice == '4':
            launch_app(targets, "spotify")
        elif choice == '5':
            if not HAS_LAUNCH_APP:
                print(f"{Fore.YELLOW}Launch app not supported{Style.RESET_ALL}")
            else:
                app_id = input(f"{Fore.CYAN}Enter app ID: {Style.RESET_ALL}").strip()
                content_id = input(f"{Fore.CYAN}Enter content ID (optional): {Style.RESET_ALL}").strip() or None
                launch_app(targets, app_id, content_id)
        elif choice == '6':
            quit_app(targets)
        input(f"{Fore.YELLOW}Press Enter...{Style.RESET_ALL}")

def device_menu():
    """Device management submenu (reboot, etc.)."""
    while True:
        clear_screen()
        print_banner()
        print(f"{Fore.CYAN}=== Device Management ==={Style.RESET_ALL}\n")
        print(f"{Fore.RED}[1]{Fore.YELLOW} Reboot device(s)")
        print(f"{Fore.RED}[2]{Fore.YELLOW} Back")
        choice = input(f"{Fore.GREEN}Select: {Style.RESET_ALL}").strip()
        if choice == '2':
            break
        targets = select_multiple_devices()
        if not targets:
            continue
        if choice == '1':
            reboot_device(targets)
        input(f"{Fore.YELLOW}Press Enter...{Style.RESET_ALL}")

def cast_menu():
    """Custom media casting submenu."""
    while True:
        clear_screen()
        print_banner()
        print(f"{Fore.CYAN}=== Cast Media ==={Style.RESET_ALL}\n")
        print(f"{Fore.RED}[1]{Fore.YELLOW} Cast from URL")
        print(f"{Fore.RED}[2]{Fore.YELLOW} Cast local file")
        print(f"{Fore.RED}[3]{Fore.YELLOW} Back")
        choice = input(f"{Fore.GREEN}Select: {Style.RESET_ALL}").strip()
        if choice == '3':
            break
        targets = select_multiple_devices()
        if not targets:
            continue
        if choice == '1':
            url = input(f"{Fore.CYAN}Media URL: {Style.RESET_ALL}").strip()
            if url:
                cast_media(targets, url)
        elif choice == '2':
            path = input(f"{Fore.CYAN}Local file path: {Style.RESET_ALL}").strip()
            if os.path.isfile(path):
                cast_local_file(targets, path)
            else:
                print(f"{Fore.RED}File not found{Style.RESET_ALL}")
        input(f"{Fore.YELLOW}Press Enter...{Style.RESET_ALL}")

def schedule_menu():
    """Scheduled actions submenu."""
    while True:
        clear_screen()
        print_banner()
        print(f"{Fore.CYAN}=== Scheduled Actions ==={Style.RESET_ALL}\n")
        print(f"{Fore.RED}[1]{Fore.YELLOW} Schedule one-time kick")
        print(f"{Fore.RED}[2]{Fore.YELLOW} Schedule recurring kick (every N seconds)")
        print(f"{Fore.RED}[3]{Fore.YELLOW} Stop all scheduled jobs")
        print(f"{Fore.RED}[4]{Fore.YELLOW} Back")
        choice = input(f"{Fore.GREEN}Select: {Style.RESET_ALL}").strip()
        if choice == '4':
            break
        if choice == '1':
            try:
                time_str = input(f"{Fore.CYAN}Enter time (HH:MM, 24h): {Style.RESET_ALL}").strip()
                now = datetime.now()
                target = datetime.strptime(time_str, "%H:%M").replace(year=now.year, month=now.month, day=now.day)
                if target < now:
                    target += timedelta(days=1)
                targets = select_multiple_devices("Select devices to kick: ")
                if targets:
                    schedule_action(kick_devices, [targets], target)
            except Exception as e:
                print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        elif choice == '2':
            try:
                interval = int(input(f"{Fore.CYAN}Interval in seconds: {Style.RESET_ALL}").strip())
                targets = select_multiple_devices("Select devices to kick: ")
                if targets:
                    schedule_recurring(kick_devices, [targets], interval)
                    if not scheduler_thread_running and SCHEDULE_AVAILABLE:
                        t = threading.Thread(target=run_scheduler)
                        t.daemon = True
                        t.start()
            except Exception as e:
                print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        elif choice == '3':
            stop_scheduler()
            print(f"{Fore.GREEN}Scheduler stopped{Style.RESET_ALL}")
        input(f"{Fore.YELLOW}Press Enter...{Style.RESET_ALL}")

def settings_menu():
    """Configuration settings submenu."""
    global config
    while True:
        clear_screen()
        print_banner()
        print(f"{Fore.CYAN}=== Settings ==={Style.RESET_ALL}\n")
        anon = config["settings"].get("anonymity", False)
        jitter = config["settings"].get("random_jitter", False)
        auto_save = config["settings"].get("auto_save", True)
        track_mac = config["settings"].get("track_mac", False)
        monitor = config["settings"].get("monitor_enabled", False)
        print(f"{Fore.RED}[1]{Fore.YELLOW} Toggle anonymity mode (currently {Fore.GREEN}{anon}{Style.RESET_ALL})")
        print(f"{Fore.RED}[2]{Fore.YELLOW} Toggle random jitter (currently {Fore.GREEN}{jitter}{Style.RESET_ALL})")
        print(f"{Fore.RED}[3]{Fore.YELLOW} Toggle auto-save (currently {Fore.GREEN}{auto_save}{Style.RESET_ALL})")
        print(f"{Fore.RED}[4]{Fore.YELLOW} Toggle MAC tracking (currently {Fore.GREEN}{track_mac}{Style.RESET_ALL})")
        print(f"{Fore.RED}[5]{Fore.YELLOW} Toggle status monitor (currently {Fore.GREEN}{monitor}{Style.RESET_ALL})")
        print(f"{Fore.RED}[6]{Fore.YELLOW} Save configuration now")
        print(f"{Fore.RED}[7]{Fore.YELLOW} Back")
        choice = input(f"{Fore.GREEN}Select: {Style.RESET_ALL}").strip()
        if choice == '7':
            save_config()
            break
        elif choice == '1':
            config["settings"]["anonymity"] = not anon
        elif choice == '2':
            config["settings"]["random_jitter"] = not jitter
        elif choice == '3':
            config["settings"]["auto_save"] = not auto_save
        elif choice == '4':
            config["settings"]["track_mac"] = not track_mac
        elif choice == '5':
            new_state = not monitor
            config["settings"]["monitor_enabled"] = new_state
            if new_state:
                start_monitor()
            else:
                stop_monitor()
        elif choice == '6':
            save_config()
        input(f"{Fore.YELLOW}Press Enter...{Style.RESET_ALL}")

def saved_devices_menu():
    """Manage persistent device database."""
    while True:
        clear_screen()
        print_banner()
        print(f"{Fore.CYAN}=== Manage Saved Devices ==={Style.RESET_ALL}\n")
        print(f"{Fore.RED}[1]{Fore.YELLOW} Save current devices to database")
        print(f"{Fore.RED}[2]{Fore.YELLOW} Load devices from database (replaces current list)")
        print(f"{Fore.RED}[3]{Fore.YELLOW} Add device manually (by IP)")
        print(f"{Fore.RED}[4]{Fore.YELLOW} View saved devices info")
        print(f"{Fore.RED}[5]{Fore.YELLOW} Rename a saved device (set friendly name)")
        print(f"{Fore.RED}[6]{Fore.YELLOW} Back")
        print(f"{Fore.CYAN}═══════════════════════════════════════════════════════")
        print(f"{Fore.GREEN}Current devices: {len(devices)}{Style.RESET_ALL}")

        choice = input(f"{Fore.GREEN}Select an option (1-6): {Style.RESET_ALL}").strip()
        if choice == '6':
            break
        elif choice == '1':
            save_config()
        elif choice == '2':
            load_devices_from_db()
        elif choice == '3':
            ip = input(f"{Fore.CYAN}Enter IP address: {Style.RESET_ALL}").strip()
            if ip:
                cast = create_chromecast_from_ip(ip)
                if cast:
                    devices.append(cast)
                    if config["settings"].get("auto_save", True):
                        save_config()
        elif choice == '4':
            print(f"{Fore.CYAN}Saved devices in database:{Style.RESET_ALL}")
            for dev_info in config.get("devices", []):
                friendly = dev_info.get('friendly_name') or dev_info.get('name', 'Unknown')
                ip = dev_info.get('ip')
                last = dev_info.get('last_seen', 'never')
                print(f"  {Fore.GREEN}{friendly}{Style.RESET_ALL} ({ip}) - Last seen: {last}")
                if config["settings"].get("track_mac", False) and dev_info.get('mac'):
                    print(f"    MAC: {dev_info['mac']}")
        elif choice == '5':
            saved = config.get("devices", [])
            if not saved:
                print(f"{Fore.YELLOW}No saved devices.{Style.RESET_ALL}")
                input("Press Enter...")
                continue
            print("Select device to rename:")
            for i, dev in enumerate(saved, 1):
                friendly = dev.get('friendly_name') or dev.get('name', 'Unknown')
                print(f"  {Fore.RED}[{i}]{Style.RESET_ALL} {friendly} ({dev.get('ip')})")
            try:
                idx = int(input("Enter number: ").strip())
                if 1 <= idx <= len(saved):
                    new_name = input("Enter new friendly name: ").strip()
                    if new_name:
                        saved[idx-1]['friendly_name'] = new_name
                        save_config()
                        print(f"{Fore.GREEN}Name updated.{Style.RESET_ALL}")
                else:
                    print("Invalid index.")
            except:
                print("Invalid input.")
            input("Press Enter...")
        input(f"{Fore.YELLOW}Press Enter...{Style.RESET_ALL}")

def group_menu():
    """Group management submenu."""
    while True:
        clear_screen()
        print_banner()
        print(f"{Fore.CYAN}=== Group Management ==={Style.RESET_ALL}\n")
        print(f"{Fore.RED}[1]{Fore.YELLOW} List all groups")
        print(f"{Fore.RED}[2]{Fore.YELLOW} Create new group")
        print(f"{Fore.RED}[3]{Fore.YELLOW} Delete group")
        print(f"{Fore.RED}[4]{Fore.YELLOW} Add device to group")
        print(f"{Fore.RED}[5]{Fore.YELLOW} Remove device from group")
        print(f"{Fore.RED}[6]{Fore.YELLOW} Kick group")
        print(f"{Fore.RED}[7]{Fore.YELLOW} Back")
        choice = input(f"{Fore.GREEN}Select: {Style.RESET_ALL}").strip()
        if choice == '7':
            save_config()
            break
        elif choice == '1':
            list_groups()
        elif choice == '2':
            name = input("Enter group name: ").strip()
            if name:
                create_group(name)
        elif choice == '3':
            name = input("Enter group name to delete: ").strip()
            if name:
                delete_group(name)
        elif choice == '4':
            name = input("Enter group name: ").strip()
            if name not in groups:
                print(f"{Fore.RED}Group not found{Style.RESET_ALL}")
            else:
                ip = input("Enter device IP: ").strip()
                if ip:
                    add_to_group(name, ip)
        elif choice == '5':
            name = input("Enter group name: ").strip()
            if name not in groups:
                print(f"{Fore.RED}Group not found{Style.RESET_ALL}")
            else:
                ip = input("Enter device IP: ").strip()
                if ip:
                    remove_from_group(name, ip)
        elif choice == '6':
            name = input("Enter group name to kick: ").strip()
            if name:
                kick_group(name)
        input(f"{Fore.YELLOW}Press Enter...{Style.RESET_ALL}")

def export_import_menu():
    """Export/import device list."""
    while True:
        clear_screen()
        print_banner()
        print(f"{Fore.CYAN}=== Export/Import Devices ==={Style.RESET_ALL}\n")
        print(f"{Fore.RED}[1]{Fore.YELLOW} Export devices to file")
        print(f"{Fore.RED}[2]{Fore.YELLOW} Import devices from file")
        print(f"{Fore.RED}[3]{Fore.YELLOW} Back")
        choice = input(f"{Fore.GREEN}Select: {Style.RESET_ALL}").strip()
        if choice == '3':
            break
        elif choice == '1':
            filename = input("Enter filename to export (e.g., devices.json): ").strip()
            if filename:
                export_devices(filename)
        elif choice == '2':
            filename = input("Enter filename to import: ").strip()
            if filename:
                import_devices(filename)
        input(f"{Fore.YELLOW}Press Enter...{Style.RESET_ALL}")

# -------------------- Main Program --------------------
def refresh_devices():
    """Update the global devices list by re-scanning."""
    cleanup_resources()
    new_devices = discover_devices()
    devices.extend(new_devices)
    return devices

def discover_devices(timeout=DEFAULT_TIMEOUT):
    """Discover Chromecasts and return a list of Chromecast objects."""
    global browser, zeroconf_instance
    stop_spinner = threading.Event()
    spinner_thread = threading.Thread(target=spinner_animation, args=(stop_spinner,))
    spinner_thread.daemon = True
    spinner_thread.start()

    casts = []
    try:
        casts, browser = pychromecast.get_chromecasts(timeout=timeout)
        if browser and hasattr(browser, 'zc'):
            zeroconf_instance = browser.zc
        for cast in casts[:]:
            try:
                cast.wait(timeout=3)
            except Exception:
                casts.remove(cast)
    except Exception as e:
        log_message(f"{Fore.RED}[!] Discovery error: {e}{Style.RESET_ALL}", level="error")
    finally:
        stop_spinner.set()
        spinner_thread.join(timeout=1)
    return casts

def ip_range_scan(network):
    """Scan an IP range (CIDR) for potential Chromecasts using ping."""
    try:
        from ipaddress import ip_network
        net = ip_network(network, strict=False)
    except ImportError:
        log_message(f"{Fore.RED}[-] ipaddress module not available. Install Python 3.3+{Style.RESET_ALL}", level="error")
        return []
    except Exception as e:
        log_message(f"{Fore.RED}[-] Invalid network: {e}{Style.RESET_ALL}", level="error")
        return []

    log_message(f"{Fore.CYAN}[>] Scanning {network}...{Style.RESET_ALL}")
    found_ips = []
    def ping_host(ip):
        try:
            if os.name == 'nt':
                result = subprocess.run(['ping', '-n', '1', '-w', '1000', str(ip)], capture_output=True, text=True)
            else:
                result = subprocess.run(['ping', '-c', '1', '-W', '1', str(ip)], capture_output=True, text=True)
            if result.returncode == 0:
                found_ips.append(str(ip))
        except:
            pass

    threads = []
    for ip in net.hosts():
        t = threading.Thread(target=ping_host, args=(ip,))
        t.start()
        threads.append(t)
        if len(threads) > 100:
            for t in threads:
                t.join()
            threads = []
    for t in threads:
        t.join()

    log_message(f"{Fore.GREEN}[+] Found {len(found_ips)} responsive IPs{Style.RESET_ALL}")
    new_devices = []
    for ip in found_ips:
        cast = create_chromecast_from_ip(ip, timeout=3)
        if cast:
            new_devices.append(cast)
    return new_devices

def main():
    global devices, browser, config

    # Already printed Python info at top

    # Load config
    load_config()

    # Legal disclaimer
    clear_screen()
    print_banner()
    print(f"{Fore.RED}{Style.BRIGHT}[!] LEGAL DISCLAIMER{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}This tool is for EDUCATIONAL PURPOSES only.")
    print(f"Use it only on networks you own or have permission to test.{Style.RESET_ALL}\n")
    response = input(f"{Fore.CYAN}Type 'I AGREE' to continue: {Style.RESET_ALL}")
    if response.strip().upper() != "I AGREE":
        print(f"{Fore.RED}Exiting.{Style.RESET_ALL}")
        sys.exit(0)

    # Auto-load saved devices if any
    if config.get("devices"):
        print(f"\n{Fore.CYAN}[>] Found saved devices. Loading...{Style.RESET_ALL}")
        load_devices_from_db()
    else:
        print(f"\n{Fore.CYAN}[>] Scanning for devices...{Style.RESET_ALL}")
        refresh_devices()
        print(f"{Fore.GREEN}[+] Found {len(devices)} devices.{Style.RESET_ALL}")
    time.sleep(1)

    # Start monitor if enabled
    if config["settings"].get("monitor_enabled", False):
        start_monitor()

    while True:
        clear_screen()
        print_banner()
        print(f"{Fore.RED}[1]{Fore.YELLOW} Scan (refresh devices)")
        print(f"{Fore.RED}[2]{Fore.YELLOW} IP Range Scan (manual)")
        print(f"{Fore.RED}[3]{Fore.YELLOW} List all devices")
        print(f"{Fore.RED}[4]{Fore.YELLOW} Kick (stop casting)")
        print(f"{Fore.RED}[5]{Fore.YELLOW} Continuous kick loop")
        print(f"{Fore.RED}[6]{Fore.YELLOW} Volume Control")
        print(f"{Fore.RED}[7]{Fore.YELLOW} Playback Control")
        print(f"{Fore.RED}[8]{Fore.YELLOW} App Management")
        print(f"{Fore.RED}[9]{Fore.YELLOW} Device Management (reboot)")
        print(f"{Fore.RED}[10]{Fore.YELLOW} Cast Media")
        print(f"{Fore.RED}[11]{Fore.YELLOW} Scheduled Actions")
        print(f"{Fore.RED}[12]{Fore.YELLOW} Manage Saved Devices")
        print(f"{Fore.RED}[13]{Fore.YELLOW} Settings")
        print(f"{Fore.RED}[14]{Fore.YELLOW} Kick from saved devices (Experimental)")
        print(f"{Fore.RED}[15]{Fore.YELLOW} Group Management")
        print(f"{Fore.RED}[16]{Fore.YELLOW} Export/Import Devices")
        print(f"{Fore.RED}[17]{Fore.YELLOW} Exit")
        print(f"{Fore.CYAN}═══════════════════════════════════════════════════════")
        print(f"{Fore.GREEN}Devices in memory: {len(devices)}{Style.RESET_ALL}")
        mon_status = "ON" if monitor_thread_running else "OFF"
        print(f"{Fore.CYAN}Status Monitor: {mon_status}{Style.RESET_ALL}")

        choice = input(f"{Fore.GREEN}Select an option (1-17): {Style.RESET_ALL}").strip()

        if choice == '1':
            scan_menu()
        elif choice == '2':
            ip_range_scan_menu()
        elif choice == '3':
            list_detailed_menu()
        elif choice == '4':
            kick_menu()
        elif choice == '5':
            continuous_kick_menu()
        elif choice == '6':
            volume_menu()
        elif choice == '7':
            playback_menu()
        elif choice == '8':
            app_menu()
        elif choice == '9':
            device_menu()
        elif choice == '10':
            cast_menu()
        elif choice == '11':
            schedule_menu()
        elif choice == '12':
            saved_devices_menu()
        elif choice == '13':
            settings_menu()
        elif choice == '14':
            kick_from_saved_menu()
        elif choice == '15':
            group_menu()
        elif choice == '16':
            export_import_menu()
        elif choice == '17':
            stop_scheduler()
            stop_monitor()
            cleanup_resources()
            save_config()
            print(f"{Fore.RED}Exiting... Goodbye.{Style.RESET_ALL}")
            break
        else:
            print(f"{Fore.RED}[!] Invalid option.{Style.RESET_ALL}")
            time.sleep(1)

if __name__ == "__main__":
    main()
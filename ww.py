import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import traceback
import os
import re
import time
import psutil
import subprocess
import ctypes
from launch_utils import log_message, has_internet
from discord_utils import find_discord_path, get_discord_pid, launch_discord, capture_discord_logs

# Debug: Log script start
log_message("Starting ww.py execution")

def discord_wiggle():
    try:
        log_message("Entering discord_wiggle")
        discord_pid = get_discord_pid()
        if discord_pid:
            try:
                process = psutil.Process(discord_pid)
                discord_path = process.exe()
                subprocess.run([discord_path, "--"], shell=False, creationflags=subprocess.DETACHED_PROCESS)
                log_message(f"Attempted to restore Discord window for PID: {discord_pid}")
            except psutil.NoSuchProcess:
                log_message(f"Discord PID {discord_pid} no longer exists")
            except Exception as e:
                log_message(f"Failed to restore Discord window: {str(e)}")
        else:
            discord_path = find_discord_path()
            if discord_path:
                discord_pid = launch_discord(discord_path)
                if not discord_pid:
                    log_message("Failed to get Discord PID after launch")
            else:
                log_message("Cannot launch Discord: No executable found")

        if discord_pid:
            try:
                channel_url = "discord://-/channels/866514085462147112/channel-browser"
                subprocess.run(["start", "", channel_url], shell=True, check=True)
                log_message(f"Activated Discord by opening DM channel for PID: {discord_pid}")
                time.sleep(5)
            except subprocess.CalledProcessError:
                log_message("Failed to open Discord DM channel")
            except Exception as e:
                log_message(f"Error activating Discord: {str(e)}")
        else:
            log_message("No Discord PID available to activate")

        if discord_pid:
            try:
                end_time = time.time() + 30
                while time.time() < end_time:
                    capture_discord_logs(output_file="discord_output.txt")
                    log_message("Checked Discord logs during activity")
                    time.sleep(2)
            except Exception as e:
                log_message(f"Error capturing Discord logs: {str(e)}")

    except Exception as e:
        log_message(f"Error in discord_wiggle: {str(e)}\n{traceback.format_exc()}")
    finally:
        root.destroy()
        log_message("Exiting discord_wiggle")

def get_idle_time():
    """Return seconds since last user input (keyboard/mouse)."""
    log_message("Entering get_idle_time")
    try:
        class LASTINPUTINFO(ctypes.Structure):
            _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

        last_input = LASTINPUTINFO()
        last_input.cbSize = ctypes.sizeof(LASTINPUTINFO)
        ctypes.windll.user32.GetLastInputInfo(ctypes.byref(last_input))
        
        # System uptime in milliseconds
        tick_count = ctypes.windll.kernel32.GetTickCount()
        
        # Idle time in seconds
        idle_time = (tick_count - last_input.dwTime) / 1000.0
        log_message(f"Idle time: {idle_time:.2f} seconds")
        return idle_time
    except Exception as e:
        log_message(f"Error in get_idle_time: {str(e)}")
        return None

def get_discord_idle_time():
    """Return seconds since Discord was opened or last interacted with, or 3600 if not running."""
    log_message("Entering get_discord_idle_time")
    try:
        # Find Discord process
        discord_pid = None
        for proc in psutil.process_iter(['name', 'pid']):
            if proc.info['name'].lower() == 'discord.exe':
                discord_pid = proc.info['pid']
                break
        
        if not discord_pid:
            log_message("No running Discord process found, assuming idle for 1 hour")
            return 3600.0  # 1 hour in seconds

        # Get Discord log directory
        log_dir = os.path.expanduser(r"~\AppData\Roaming\Discord\logs")
        if not os.path.exists(log_dir):
            log_message(f"Discord log directory not found: {log_dir}")
            return 3600.0  # Treat as not running if logs are missing

        # Find the latest log file
        log_files = [os.path.join(log_dir, f) for f in os.listdir(log_dir) if f.endswith('.log')]
        if not log_files:
            log_message("No Discord log files found")
            return 3600.0  # Treat as not running if no logs

        latest_log = max(log_files, key=os.path.getmtime)
        
        # Read the last line with a timestamp
        timestamp_pattern = r"\[(\d{2}:\d{2}:\d{2}\.\d{3})\]"
        last_timestamp = None
        with open(latest_log, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in reversed(lines):  # Read from end for efficiency
                match = re.search(timestamp_pattern, line)
                if match:
                    last_timestamp = match.group(1)  # e.g., "12:40:24.407"
                    break
        
        if not last_timestamp:
            log_message(f"No timestamp found in Discord log: {latest_log}")
            process = psutil.Process(discord_pid)
            create_time = process.create_time()
            idle_time = time.time() - create_time
            log_message(f"Discord (PID: {discord_pid}) last active {idle_time:.2f} seconds ago (using process creation)")
            return idle_time

        # Parse timestamp (assume same day for simplicity)
        current_time = time.time()
        current_date = datetime.now().date()
        timestamp_dt = datetime.strptime(f"{current_date} {last_timestamp}", "%Y-%m-%d %H:%M:%S.%f")
        last_interaction = timestamp_dt.timestamp()

        # Handle case where log is from previous day (e.g., past midnight)
        if last_interaction > current_time:
            last_interaction -= 86400  # Subtract 1 day in seconds

        # Seconds since last interaction
        idle_time = current_time - last_interaction
        log_message(f"Discord (PID: {discord_pid}) last active {idle_time:.2f} seconds ago")
        return idle_time

    except psutil.NoSuchProcess:
        log_message(f"Discord process (PID: {discord_pid}) no longer exists")
        return None
    except Exception as e:
        log_message(f"Error checking Discord idle time: {str(e)}")
        return None

if __name__ == "__main__":
    try:
        log_message(f"Script started with pythonw (PID: {os.getpid()})")
        
        # Explicitly initialize GUI
        root = tk.Tk()
        root.attributes('-topmost', True)
        root.withdraw()
        log_message("GUI initialized")
        
        messagebox.showinfo("WorkWiggle", f"Script ran at {datetime.now()}")
        log_message("Pop-up shown")
        
        # Wait loop for 10 seconds
        log_message("Starting wait loop")
        time.sleep(2)
        log_message("Wait loop completed")
        
        # Check for internet access
        log_message("Checking for internet access")
        while not has_internet():
            log_message("No internet access, waiting 5 seconds")
            time.sleep(2)
        
        log_message("Internet access confirmed")

        # Print idle times
        idle_time = get_idle_time()
        log_message(f"System idle time: {idle_time}")
        discord_idle = get_discord_idle_time()
        log_message(f"Discord idle time: {discord_idle}")
        print(discord_idle)

        # Run Discord wiggle
        log_message("Calling discord_wiggle")
        discord_wiggle()
        log_message("Finished discord_wiggle")

    except Exception as e:
        log_message(f"Error in main: {str(e)}\n{traceback.format_exc()}")
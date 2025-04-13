import tkinter as tk
from tkinter import messagebox
from datetime import datetime, timedelta
import traceback
import os
import re
import time
import psutil
import subprocess
import ctypes
import random
import numpy as np  # For lognormal distribution
from launch_utils import log_message, has_internet
from discord_utils import find_discord_path, get_discord_pid, launch_discord, capture_discord_logs

# Configurable variables
END_TIME_MEAN_HOURS = 17.25  # 5:15 PM (17:15 in 24-hour format)
END_TIME_STD_MINUTES = 30    # 30 minutes
CHECK_INTERVAL_SECONDS = 30   # Check idle times every 30 seconds
IDLE_TIME_THRESHOLD_SECONDS = 300  # Call discord_wiggle if system idle > 300 seconds
DISCORD_IDLE_THRESHOLD_SECONDS = 500  # Call discord_wiggle if Discord idle > 500 seconds
DELAY_MEAN_SECONDS = 60      # Mean delay before discord_wiggle
DELAY_STD_SECONDS = 30       # Std dev for delay

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
                # List of channel URLs
                channel_urls = [
                    "discord://-/channels/866514085462147112/1313162988118605835",
                    "discord://-/channels/@me/1105197989192011897/1329857957323870279",
                    "discord://-/channels/866514085462147112/1360014770077569177",
                    "discord://-/channels/866514085462147112/1354895636004343972",
                    "discord://-/channels/866514085462147112/1014930559618797579"
                ]
                # Pick a random channel
                channel_url = random.choice(channel_urls)
                subprocess.run(["start", "", channel_url], shell=True, check=True)
                log_message(f"Activated Discord by opening channel {channel_url} for PID: {discord_pid}")
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
    """Return seconds since last specified Discord action in discord_output.txt."""
    log_message("Entering get_discord_idle_time")
    try:
        output_file = "discord_output.txt"
        if not os.path.exists(output_file):
            log_message(f"Output file not found: {output_file}")
            return 3600.0  # Assume idle for 1 hour if no file

        # List of actions to track (extendable)
        actions = [
            r"\[Routing/Utils\] transitionTo -",
            r"\[KeyboardLayoutMapUtils\] KeyboardMapper -"
        ]
        
        latest_timestamp = None
        timestamp_pattern = r"(\d{2}:\d{2}:\d{2}\.\d{3})"
        
        with open(output_file, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
            for line in reversed(lines):  # Read from end for efficiency
                if any(re.search(action, line) for action in actions):
                    match = re.search(timestamp_pattern, line)
                    if match:
                        latest_timestamp = match.group(1)
                        break
        
        if not latest_timestamp:
            log_message("No matching action found in discord_output.txt")
            return 3600.0  # Assume idle for 1 hour if no action

        # Parse timestamp (assume same day)
        current_time = time.time()
        current_date = datetime.now().date()
        timestamp_dt = datetime.strptime(f"{current_date} {latest_timestamp}", "%Y-%m-%d %H:%M:%S.%f")
        last_interaction = timestamp_dt.timestamp()

        # Handle past midnight case
        if last_interaction > current_time:
            last_interaction -= 86400  # Subtract 1 day

        idle_time = current_time - last_interaction
        log_message(f"Last action at {latest_timestamp}, idle for {idle_time:.2f} seconds")
        return idle_time

    except Exception as e:
        log_message(f"Error checking Discord idle time: {str(e)}")
        return 3600.0  # Default to 1 hour on error

if __name__ == "__main__":
    try:
        log_message(f"Script started with pythonw (PID: {os.getpid()})")
        
        # Set random end time (lognormal distribution)
        mean_minutes = END_TIME_MEAN_HOURS * 60
        std_minutes = END_TIME_STD_MINUTES
        # Convert to lognormal parameters
        mu = np.log(mean_minutes**2 / np.sqrt(mean_minutes**2 + std_minutes**2))
        sigma = np.sqrt(np.log(1 + (std_minutes**2 / mean_minutes**2)))
        minutes_until_end = np.random.lognormal(mu, sigma)
        end_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(minutes=minutes_until_end)
        log_message(f"Set end time to {end_time.strftime('%H:%M:%S')}")

        # Initialize GUI
        root = tk.Tk()
        root.attributes('-topmost', True)
        root.withdraw()
        log_message("GUI initialized")

        # Show initial popup
        messagebox.showinfo("WorkWiggle", f"Script started at {datetime.now()}, will run until {end_time.strftime('%H:%M:%S')}")
        log_message("Pop-up shown")

        while datetime.now() < end_time:
            # Check internet access
            log_message("Checking for internet access")
            while not has_internet():
                log_message("No internet access, waiting 5 seconds")
                time.sleep(5)
            log_message("Internet access confirmed")

            # Get idle times
            idle_time = get_idle_time()
            discord_idle = get_discord_idle_time()
            log_message(f"System idle time: {idle_time}")
            log_message(f"Discord idle time: {discord_idle}")
            print(f"discord_idle: {discord_idle}")
            print(f"idle_time: {idle_time}")

            # Check thresholds and call discord_wiggle if needed
            if (idle_time is not None and idle_time > IDLE_TIME_THRESHOLD_SECONDS) or \
               (discord_idle is not None and discord_idle > DISCORD_IDLE_THRESHOLD_SECONDS):
                # Random delay (lognormal distribution)
                print("Idle thresholds exceeded, calling discord_wiggle")
                mean_delay = DELAY_MEAN_SECONDS
                std_delay = DELAY_STD_SECONDS
                mu_delay = np.log(mean_delay**2 / np.sqrt(mean_delay**2 + std_delay**2))
                sigma_delay = np.sqrt(np.log(1 + (std_delay**2 / mean_delay**2)))
                delay = np.random.lognormal(mu_delay, sigma_delay)
                log_message(f"Idle thresholds exceeded, waiting {delay:.2f} seconds before discord_wiggle")
                time.sleep(max(0, delay))  # Ensure non-negative delay
                discord_wiggle()
            
            # Wait for next check
            log_message(f"Waiting {CHECK_INTERVAL_SECONDS} seconds for next check")
            time.sleep(CHECK_INTERVAL_SECONDS)

    except Exception as e:
        log_message(f"Error in main: {str(e)}\n{traceback.format_exc()}")
    finally:
        if 'root' in locals():
            root.destroy()
        log_message("Script exiting")
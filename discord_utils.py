import os
import time
from datetime import datetime  # Ensure this import is at the top
import subprocess
import glob
import psutil
import datetime
import threading
from launch_utils import log_message

def find_discord_path():
    discord_base = r"C:\Users\Haley Thomson\AppData\Local\Discord"
    try:
        discord_exe_pattern = os.path.join(discord_base, "app-*", "Discord.exe")
        discord_exes = glob.glob(discord_exe_pattern)
        if discord_exes:
            latest_discord = max(discord_exes, key=os.path.getmtime)
            log_message(f"Found Discord executable: {latest_discord}")
            return latest_discord
        else:
            log_message("No Discord executable found in " + discord_base)
            return None
    except Exception as e:
        log_message(f"Error finding Discord path: {str(e)}")
        return None

def get_discord_pid():
    try:
        for proc in psutil.process_iter(['name', 'pid']):
            if proc.info['name'].lower() == 'discord.exe':
                log_message(f"Found running Discord process with PID: {proc.info['pid']}")
                return proc.info['pid']
        log_message("No running Discord process found")
        return None
    except Exception as e:
        log_message(f"Error checking Discord process: {str(e)}")
        return None

def launch_discord(discord_path):
    try:
        log_message(f"Attempting to launch Discord at: {discord_path}")
        output_file = "discord_output.txt"
        
        process = subprocess.Popen(
            f'"{discord_path}" > "{output_file}" 2>&1',
            shell=True,
            creationflags=subprocess.DETACHED_PROCESS
        )
        log_message(f"Launched Discord with PID: {process.pid}")
        time.sleep(2)
        discord_pid = get_discord_pid()
        if discord_pid:
            log_message(f"Discord PID found: {discord_pid}")
            return discord_pid
        return process.pid
    except Exception as e:
        log_message(f"Failed to launch Discord: {str(e)}")
        return None

def monitor_discord_logs(output_file="discord_output.txt"):
    try:
        log_dir = os.path.expanduser(r"~\AppData\Roaming\Discord\logs")
        if not os.path.exists(log_dir):
            log_message(f"Log directory not found: {log_dir}")
            return
        def get_latest_log():
            log_files = [os.path.join(log_dir, f) for f in os.listdir(log_dir) if f.endswith('.log')]
            return max(log_files, key=os.path.getmtime) if log_files else None

        latest_log = get_latest_log()
        if not latest_log:
            log_message("No Discord log files found")
            return
        
        def tail_log():
            current_log = latest_log
            with open(output_file, 'a', encoding='utf-8') as out:
                while True:
                    if get_latest_log() != current_log:  # Check for newer log file
                        current_log = get_latest_log()
                        log_message(f"Switched to new log file: {current_log}")
                    try:
                        with open(current_log, 'r', encoding='utf-8', errors='replace') as f:
                            f.seek(0, os.SEEK_END)
                            while True:
                                line = f.readline()
                                if line:
                                    line = line.strip()
                                    if line:
                                        log_message(f"Discord log: {line}")
                                        timestamp = datetime.now()
                                        out.write(f"[{timestamp.strftime('%H:%M:%S.%f')[:-3]}] {line}\n")
                                        out.flush()
                                else:
                                    time.sleep(0.1)
                    except Exception as e:
                        log_message(f"Error reading log: {str(e)}")
                        time.sleep(1)  # Retry after error

        threading.Thread(target=tail_log, daemon=True).start()
        log_message(f"Started monitoring Discord logs: {latest_log}")
    except Exception as e:
        log_message(f"Error monitoring logs: {str(e)}")


def capture_discord_logs(output_file="discord_output.txt"):
    try:
        log_message(f"Logs are being appended to {output_file} by read_output thread")
    except Exception as e:
        log_message(f"Error in capture_discord_logs: {str(e)}")
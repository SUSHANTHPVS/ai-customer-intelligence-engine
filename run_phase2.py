#!/usr/bin/env python3
"""Wrapper to run phase2_setup with automatic password input"""
import subprocess
import sys
import os
from pathlib import Path

project_root = Path(r"C:\Users\SUSHANTH\Desktop\AI Customer Intelligence Engine")
os.chdir(project_root)

# Run the setup script with password input
try:
    process = subprocess.Popen(
        [sys.executable, "phase2_setup.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Provide password
    output, _ = process.communicate(input="postgres\n", timeout=300)
    
    # Write output to file
    with open("phase2_run.log", "w") as f:
        f.write(output)
    
    print("Setup completed. Output saved to phase2_run.log")
    print("\n" + "="*60)
    print(output)
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)

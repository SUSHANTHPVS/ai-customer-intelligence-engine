#!/usr/bin/env python3
"""Initialize git and create first commit - write to file"""
import subprocess
import os

project_dir = r"C:\Users\SUSHANTH\Desktop\AI Customer Intelligence Engine"
log_file = os.path.join(project_dir, "git_setup.log")

with open(log_file, "w") as f:
    f.write(f"Project directory: {project_dir}\n\n")
    
    os.chdir(project_dir)
    
    # Initialize git
    f.write("1. Initializing git repository...\n")
    result = subprocess.run(["git", "init"], capture_output=True, text=True)
    f.write(f"   stdout: {result.stdout}\n")
    f.write(f"   stderr: {result.stderr}\n")
    f.write(f"   returncode: {result.returncode}\n\n")
    
    # Configure git user
    f.write("2. Configuring git user...\n")
    result = subprocess.run(["git", "config", "user.name", "AI Customer Intelligence"], capture_output=True, text=True)
    f.write(f"   returncode: {result.returncode}\n")
    result = subprocess.run(["git", "config", "user.email", "dev@customer-intelligence.local"], capture_output=True, text=True)
    f.write(f"   returncode: {result.returncode}\n\n")
    
    # Add all files
    f.write("3. Adding files...\n")
    result = subprocess.run(["git", "add", "."], capture_output=True, text=True)
    f.write(f"   returncode: {result.returncode}\n")
    f.write(f"   stdout: {result.stdout}\n")
    f.write(f"   stderr: {result.stderr}\n\n")
    
    # Create commit
    f.write("4. Creating commit...\n")
    result = subprocess.run(
        ["git", "commit", "-m", "Initial project setup: architecture, structure, and synthetic data generation pipeline"],
        capture_output=True, text=True
    )
    f.write(f"   returncode: {result.returncode}\n")
    f.write(f"   stdout: {result.stdout}\n")
    f.write(f"   stderr: {result.stderr}\n\n")
    
    # Show log
    f.write("5. Git log:\n")
    result = subprocess.run(["git", "log", "--oneline", "-5"], capture_output=True, text=True)
    f.write(f"   {result.stdout}\n")
    
    # Show status
    f.write("\n6. Git status:\n")
    result = subprocess.run(["git", "status"], capture_output=True, text=True)
    f.write(f"   {result.stdout}\n")
    
    f.write("\n✓ Complete\n")

print(f"Log written to {log_file}")

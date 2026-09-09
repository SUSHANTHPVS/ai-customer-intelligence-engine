#!/usr/bin/env python3
"""Initialize git and create first commit"""
import subprocess
import os
import sys

project_dir = r"C:\Users\SUSHANTH\Desktop\AI Customer Intelligence Engine"

print(f"Project directory: {project_dir}")
print(f"Current directory: {os.getcwd()}\n")

os.chdir(project_dir)

try:
    # Initialize git
    print("1. Initializing git repository...")
    result = subprocess.run(["git", "init"], capture_output=True, text=True)
    print(f"   Output: {result.stdout.strip() if result.stdout else '(no output)'}")
    if result.stderr:
        print(f"   Error: {result.stderr.strip()}")
    
    # Configure git user (if not already configured)
    print("\n2. Configuring git user...")
    subprocess.run(["git", "config", "user.name", "AI Customer Intelligence"], capture_output=True)
    subprocess.run(["git", "config", "user.email", "dev@customer-intelligence.local"], capture_output=True)
    print("   User configured")
    
    # Add all files
    print("\n3. Adding files to git...")
    result = subprocess.run(["git", "add", "."], capture_output=True, text=True)
    print(f"   Files added (output: {result.stdout.strip() if result.stdout else 'none'})")
    
    # Create initial commit
    print("\n4. Creating initial commit...")
    result = subprocess.run(
        ["git", "commit", "-m", "Initial project setup: architecture, structure, and synthetic data generation pipeline"],
        capture_output=True, text=True
    )
    print(f"   Output: {result.stdout.strip() if result.stdout else '(no output)'}")
    if result.stderr:
        print(f"   Info: {result.stderr.strip()}")
    
    # Show status
    print("\n5. Repository status:")
    result = subprocess.run(["git", "log", "--oneline", "-5"], capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    else:
        print("   (no commits yet)")
    
    # Show git status
    result = subprocess.run(["git", "status"], capture_output=True, text=True)
    print(f"\n   {result.stdout.strip()}")
    
    print("\n✓ Git initialization complete!")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    sys.exit(1)

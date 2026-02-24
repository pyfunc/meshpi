#!/usr/bin/env python3
"""
Project analysis script - converts code2logic command to Python
"""

import subprocess
import sys
import os

def run_code2logic():
    """Run code2logic analysis on the current directory"""
    cmd = [
        "code2logic",
        "./",
        "-f", "toon",
        "--compact", 
        "--function-logic",
        "--with-schema",
        "-o", "project.toon"
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Analysis completed successfully!")
        print("Output saved to: project.toon")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running code2logic: {e}")
        print(f"Stderr: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: code2logic command not found")
        print("Please install code2logic first")
        sys.exit(1)

if __name__ == "__main__":
    if not os.path.exists("./"):
        print("Error: Current directory not found")
        sys.exit(1)
    
    run_code2logic()

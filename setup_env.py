#!/usr/bin/env python3
"""
Setup script to configure the Python path for the project.
Run this script before running tests or the application if you're not installing the package.
"""
import sys
import os

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

print("Python path configured successfully!")
print(f"Added {os.path.abspath(os.path.dirname(__file__))} to sys.path")

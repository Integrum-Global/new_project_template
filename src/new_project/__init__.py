"""
App Template Package

This is a template for creating new client applications.
Copy this entire folder to start a new app.

Usage:
    cp -r src/new_project src/my_new_app
    cd src/my_new_app
    # Edit setup.py, README.md, and config.py
    # Start development!
"""

__version__ = "0.1.0"
__author__ = "Your Team"

# Import main components for easy access
from .config import AppConfig

__all__ = ["AppConfig"]
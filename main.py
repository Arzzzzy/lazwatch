# main.py
import os
import sys
from app.gui import create_gui

# Ensure the app sees the local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    create_gui()
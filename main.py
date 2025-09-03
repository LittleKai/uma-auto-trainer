#!/usr/bin/env python3
"""
Uma Musume Auto Train - Main Entry Point
Developed by LittleKai
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import UmaAutoGUI


def main():
  """Main application entry point"""
  try:
    app = UmaAutoGUI()
    app.run()
  except KeyboardInterrupt:
    print("\nApplication interrupted by user")
  except Exception as e:
    print(f"Fatal error: {e}")
    input("Press Enter to exit...")


if __name__ == "__main__":
  main()
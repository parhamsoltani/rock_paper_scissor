#!/usr/bin/env python3
"""
Advanced Rock Paper Scissors Game
Main entry point for the application
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from src.gui_manager import MainWindow

def main():
    """Initialize and run the application"""
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

    app = QApplication(sys.argv)
    app.setApplicationName("Rock Paper Scissors Advanced")

    # Set application style
    app.setStyle('Fusion')

    # Create and show main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
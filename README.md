Rock Paper Scissors Advanced An advanced implementation of the classic
Rock Paper Scissors game featuring AI opponents, real-time gesture
recognition using MediaPipe, and a modern PyQt6 interface.

Features 🎮 Game Modes VS AI: Play against intelligent AI opponents with
multiple difficulty levels Local Multiplayer: Two players using the same
device Practice Mode: Perfect your gestures without scoring 🤖 AI
Intelligence Easy: Random moves for beginners Medium: Pattern
recognition and strategic countering Hard: Advanced Markov chain
prediction and adaptive learning 👋 Gesture Recognition Real-time hand
gesture detection using MediaPipe Accurate recognition of Rock, Paper,
and Scissors gestures Visual feedback and gesture validation Fallback
manual input when camera is unavailable 📊 Statistics & Analytics
Win/loss tracking and statistics Win streak monitoring Performance
analytics Persistent data storage 🎵 Audio & Visual Sound effects for
game events Modern, responsive UI design Real-time video display Smooth
animations and transitions Requirements System Requirements Python 3.8
or higher Webcam (optional, manual input available as fallback) Windows
10/11, macOS 10.14+, or Linux Python Dependencies apache

Copy PyQt6\>=6.4.0 opencv-python\>=4.7.0 mediapipe\>=0.10.0
numpy\>=1.21.0 pygame\>=2.1.0 Installation 1. Clone the Repository bash

Copy git clone
https://github.com/yourusername/rock-paper-scissors-advanced.git cd
rock-paper-scissors-advanced 2. Create Virtual Environment (Recommended)
bash

Copy \# Windows python -m venv venv
venv`\Scripts`{=tex}`\activate`{=tex}

# macOS/Linux

python3 -m venv venv source venv/bin/activate 3. Install Dependencies
bash

Copy pip install -r requirements.txt 4. Run the Application bash

Copy python main.py How to Play Basic Gameplay Start Game: Click the
"Start Game" button Countdown: Wait for the 3-2-1 countdown Make Your
Move: When "SHOOT!" appears, show your gesture to the camera See
Results: View the outcome and updated scores Next Round: Click "Start
Game" again for the next round Gesture Recognition Rock: Make a fist
(all fingers closed) Paper: Open hand (all fingers extended) Scissors:
Peace sign (index and middle finger extended) Game Controls Difficulty:
Choose Easy, Medium, or Hard AI Mode: Select VS AI or Local Multiplayer
Reset: Clear scores and start fresh Statistics: View your performance
history Project Structure angelscript

Copy rock_paper_scissors/ ├── main.py \# Application entry point ├──
config.json \# Configuration settings ├── requirements.txt \# Python
dependencies ├── README.md \# This file ├── src/ \# Source code │ ├──
**init**.py │ ├── game_engine.py \# Core game logic │ ├──
hand_detector.py \# MediaPipe gesture recognition │ ├── gui_manager.py
\# PyQt6 user interface │ ├── sound_manager.py \# Audio management │ ├──
ai_player.py \# AI opponents │ ├── network_manager.py \# Multiplayer
networking │ └── utils.py \# Utility functions ├── data/ \# Game data
storage │ ├── stats.json \# Player statistics │ └── leaderboard.json \#
High scores ├── assets/ \# Game assets │ ├── sounds/ \# Sound effects │
└── images/ \# UI icons and images └── tests/ \# Unit tests ├──
**init**.py └── test_game_engine.py Configuration Edit config.json to
customize game settings:

json

Copy { "video": { "camera_index": 0, "resolution": \[640, 480\], "fps":
30 }, "game": { "countdown_duration": 3, "rounds_per_game": 5,
"detection_confidence": 0.7 }, "audio": { "effects_volume": 0.5,
"music_volume": 0.3, "enabled": true } } Troubleshooting Camera Issues
No camera detected: The game will automatically switch to manual input
mode Poor gesture recognition: Ensure good lighting and clear hand
positioning Camera permission: Grant camera access when prompted
Performance Issues Lower the camera resolution in config.json Reduce the
FPS setting Close other applications using the camera Installation
Issues Ensure Python 3.8+ is installed Try updating pip: pip install
--upgrade pip On Linux, you may need: sudo apt-get install python3-pyqt6
Development Running Tests bash

Copy python -m pytest tests/ Adding New Features Fork the repository
Create a feature branch Implement your changes Add tests for new
functionality Submit a pull request Code Style Follow PEP 8 guidelines
Use type hints where possible Document functions and classes Keep
functions focused and modular AI Implementation Details Pattern
Recognition The AI analyzes your move history to identify patterns and
predict future moves:

Sequence Analysis: Looks for repeated move sequences Frequency Analysis:
Tracks most common moves Adaptive Learning: Adjusts strategy based on
player behavior Difficulty Levels Easy (Random): 33% win rate - purely
random moves Medium (Strategic): 45-55% win rate - basic pattern
recognition Hard (Predictive): 60-70% win rate - advanced prediction
algorithms Statistics Tracking The game automatically tracks:

Total games played Win/loss/draw counts Current and best win streaks
Move frequency analysis Performance over time Data is stored locally in
JSON format and persists between sessions.

Contributing We welcome contributions! Please see our contributing
guidelines:

Check existing issues and pull requests Fork the repository Create a
descriptive branch name Make your changes with appropriate tests Update
documentation as needed Submit a pull request with a clear description
License This project is licensed under the MIT License - see the LICENSE
file for details.

Acknowledgments MediaPipe: Google's framework for building perception
pipelines PyQt6: Cross-platform GUI toolkit OpenCV: Computer vision
library NumPy: Scientific computing library Version History v2.0.0
(Current)

Complete rewrite with improved gesture recognition Enhanced AI with
multiple difficulty levels Modern PyQt6 interface Comprehensive
statistics tracking Better error handling and user experience v1.0.0

Initial release with basic functionality Simple gesture recognition
Basic AI opponent Support If you encounter any issues or have questions:

Check the troubleshooting section above Search existing GitHub issues
Create a new issue with detailed information Include your system
information and error messages Future Enhancements Online multiplayer
with matchmaking Tournament mode with brackets Advanced statistics and
analytics Custom gesture training Mobile app version Voice commands
integration Enjoy playing Rock Paper Scissors Advanced! 🎮✂️📄🗿

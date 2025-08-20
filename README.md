# Rock Paper Scissors Game! 

Classic Rock Paper Scissors game featuring AI opponents, real-time gesture recognition using MediaPipe, and a modern PyQt6 interface.  

---

## Features  

### Game Modes  
- VS AI: Play against intelligent AI opponents with multiple difficulty levels  
- Local Multiplayer: Two players using the same device  
- Practice Mode: Perfect your gestures without scoring  

### AI Intelligence  
- Easy: Random moves for beginners  
- Medium: Pattern recognition and strategic countering  
- Hard: Advanced Markov chain prediction and adaptive learning  

### Gesture Recognition  
- Real-time hand gesture detection using MediaPipe  
- Accurate recognition of Rock, Paper, and Scissors gestures  
- Visual feedback and gesture validation  
- Fallback manual input when camera is unavailable  


### Audio & Visual  
- Sound effects for game events  
- Modern, responsive UI design  
- Real-time video display  
- Smooth animations and transitions  

---

## Requirements  

**System Requirements**  
- Python 3.8 or higher  
- Webcam (optional, manual input available as fallback)  


**Python Dependencies**  
- PyQt6 >= 6.4.0  
- opencv-python >= 4.7.0  
- mediapipe >= 0.10.0  
- numpy >= 1.21.0  
- pygame >= 2.1.0  

---

## Installation  

1. Clone the Repository:  
```bash
git clone https://github.com/yourusername/rock-paper-scissors-advanced.git
cd rock-paper-scissors-advanced
```
2. Create Virtual Environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```
3. Install Dependencies:
```bash
pip install -r requirements.txt
```
4. Run the Application:
```bash
python main.py
```

# Configuration
Edit config.json to customize game settings:
```json
{
  "video": {
    "camera_index": 0,
    "resolution": [640, 480],
    "fps": 30
  },
  "game": {
    "countdown_duration": 3,
    "rounds_per_game": 5,
    "detection_confidence": 0.7
  },
  "audio": {
    "effects_volume": 0.5,
    "music_volume": 0.3,
    "enabled": true
  }
}
```

# Developements
Running Tests
```bash
python -m pytest tests/
```

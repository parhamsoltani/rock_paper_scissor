"""
Utility functions and helpers
"""

import os
import json
import logging
import hashlib
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('game.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def ensure_directory(path: str) -> None:
    """Ensure directory exists, create if not"""
    Path(path).mkdir(parents=True, exist_ok=True)

def load_json_file(file_path: str, default: Any = None) -> Any:
    """Load JSON file with error handling"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logging.error(f"Error loading {file_path}: {e}")
    return default or {}

def save_json_file(file_path: str, data: Any) -> bool:
    """Save data to JSON file with error handling"""
    try:
        ensure_directory(os.path.dirname(file_path))
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except (IOError, TypeError) as e:
        logging.error(f"Error saving {file_path}: {e}")
        return False

def generate_session_id() -> str:
    """Generate unique session ID"""
    timestamp = str(time.time())
    return hashlib.md5(timestamp.encode()).hexdigest()[:8]

def format_duration(seconds: float) -> str:
    """Format duration in human readable format"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

def calculate_statistics(wins: int, losses: int, draws: int) -> Dict[str, float]:
    """Calculate game statistics"""
    total_games = wins + losses + draws
    if total_games == 0:
        return {
            "win_rate": 0.0,
            "loss_rate": 0.0,
            "draw_rate": 0.0,
            "total_games": 0
        }

    return {
        "win_rate": (wins / total_games) * 100,
        "loss_rate": (losses / total_games) * 100,
        "draw_rate": (draws / total_games) * 100,
        "total_games": total_games
    }

def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and sanitize configuration"""
    default_config = {
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
            "enabled": True
        },
        "network": {
            "default_port": 5555,
            "timeout": 10
        }
    }

    # Merge with defaults
    for section, values in default_config.items():
        if section not in config:
            config[section] = values
        else:
            for key, default_value in values.items():
                if key not in config[section]:
                    config[section][key] = default_value

    return config

def get_asset_path(asset_type: str, filename: str) -> str:
    """Get full path to asset file"""
    base_path = os.path.join("assets", asset_type)
    return os.path.join(base_path, filename)

def benchmark_function(func, *args, **kwargs) -> tuple:
    """Benchmark function execution time"""
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    execution_time = end_time - start_time
    return result, execution_time

class PerformanceMonitor:
    """Monitor game performance metrics"""

    def __init__(self):
        self.start_time = time.time()
        self.frame_times = []
        self.max_samples = 100

    def update_frame_time(self, frame_time: float):
        """Update frame time measurement"""
        self.frame_times.append(frame_time)
        if len(self.frame_times) > self.max_samples:
            self.frame_times.pop(0)

    def get_fps(self) -> float:
        """Calculate current FPS"""
        if not self.frame_times:
            return 0.0
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        return 1.0 / avg_frame_time if avg_frame_time > 0 else 0.0

    def get_session_duration(self) -> float:
        """Get current session duration"""
        return time.time() - self.start_time

    def reset(self):
        """Reset performance monitoring"""
        self.start_time = time.time()
        self.frame_times = []

class ConfigManager:
    """Manage application configuration"""

    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        config = load_json_file(self.config_file, {})
        return validate_config(config)

    def save_config(self) -> bool:
        """Save configuration to file"""
        return save_json_file(self.config_file, self.config)

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(section, {}).get(key, default)

    def set(self, section: str, key: str, value: Any) -> None:
        """Set configuration value"""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section"""
        return self.config.get(section, {})

def create_default_assets():
    """Create default asset directories and placeholder files"""
    directories = [
        "assets/images",
        "assets/images/icons",
        "assets/sounds",
        "data"
    ]

    for directory in directories:
        ensure_directory(directory)

    # Create placeholder files if they don't exist
    placeholder_files = {
        "data/stats.json": {
            "total_games": 0,
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "win_streak": 0,
            "best_streak": 0,
            "move_history": []
        },
        "data/leaderboard.json": []
    }

    for file_path, default_content in placeholder_files.items():
        if not os.path.exists(file_path):
            save_json_file(file_path, default_content)
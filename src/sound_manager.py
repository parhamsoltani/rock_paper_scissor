"""
Sound effects and music management
"""

import os
import pygame
from typing import Dict

class SoundManager:
    """Manage game sounds and music"""

    def __init__(self):
        try:
            pygame.mixer.init()
            self.enabled = True
        except:
            self.enabled = False

        self.sounds = {}
        self.music_volume = 0.3
        self.effects_volume = 0.5
        self.load_sounds()

    def load_sounds(self):
        """Load all sound effects - create dummy sounds if files don't exist"""
        if not self.enabled:
            return

        sound_files = {
            "click": "assets/sounds/click.wav",
            "countdown": "assets/sounds/countdown.wav",
            "win": "assets/sounds/win.wav",
            "lose": "assets/sounds/lose.wav",
            "draw": "assets/sounds/draw.wav"
        }

        for name, file_path in sound_files.items():
            if os.path.exists(file_path):
                try:
                    self.sounds[name] = pygame.mixer.Sound(file_path)
                    self.sounds[name].set_volume(self.effects_volume)
                except:
                    pass

    def play_sound(self, sound_name: str):
        """Play a sound effect"""
        if self.enabled and sound_name in self.sounds:
            try:
                self.sounds[sound_name].play()
            except:
                pass

    def set_effects_volume(self, volume: float):
        """Set effects volume (0.0 to 1.0)"""
        self.effects_volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.effects_volume)
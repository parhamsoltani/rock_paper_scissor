"""
Core game logic and rules management
"""

import json
import random
from enum import Enum
from datetime import datetime
from typing import Optional, Tuple, Dict, List
import numpy as np
import os

class Move(Enum):
    """Possible moves in the game"""
    ROCK = 1
    PAPER = 2
    SCISSORS = 3

    @classmethod
    def from_fingers(cls, finger_count: int) -> Optional['Move']:
        """Convert finger count to move"""
        mapping = {0: cls.ROCK, 5: cls.PAPER, 2: cls.SCISSORS}
        return mapping.get(finger_count)

    def beats(self, other: 'Move') -> bool:
        """Check if this move beats another"""
        winning_moves = {
            Move.ROCK: Move.SCISSORS,
            Move.PAPER: Move.ROCK,
            Move.SCISSORS: Move.PAPER
        }
        return winning_moves[self] == other

class GameMode(Enum):
    """Available game modes"""
    VS_AI = "vs_ai"
    LOCAL_MULTIPLAYER = "local_multiplayer"
    ONLINE_MULTIPLAYER = "online_multiplayer"
    TOURNAMENT = "tournament"
    PRACTICE = "practice"

class GameResult(Enum):
    """Possible game results"""
    PLAYER1_WIN = "player1_win"
    PLAYER2_WIN = "player2_win"
    DRAW = "draw"

class GameEngine:
    """Main game engine handling game logic"""

    def __init__(self):
        self.current_mode = GameMode.VS_AI
        self.scores = {"player1": 0, "player2": 0}
        self.round_history = []
        self.current_round = 0
        self.max_rounds = 5
        self.statistics = self._load_statistics()
        self.ai_difficulty = "medium"
        self.prediction_model = None

    def _load_statistics(self) -> Dict:
        """Load player statistics from file"""
        stats_file = "data/stats.json"
        if os.path.exists(stats_file):
            with open(stats_file, 'r') as f:
                return json.load(f)
        return {
            "total_games": 0,
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "win_streak": 0,
            "best_streak": 0,
            "move_history": []
        }

    def save_statistics(self):
        """Save player statistics to file"""
        os.makedirs("data", exist_ok=True)
        with open("data/stats.json", 'w') as f:
            json.dump(self.statistics, f, indent=2)

    def determine_winner(self, move1: Move, move2: Move) -> GameResult:
        """Determine the winner of a round"""
        if move1 == move2:
            return GameResult.DRAW
        elif move1.beats(move2):
            return GameResult.PLAYER1_WIN
        else:
            return GameResult.PLAYER2_WIN

    def play_round(self, player1_move: Move, player2_move: Move) -> Dict:
        """Play a single round"""
        result = self.determine_winner(player1_move, player2_move)

        # Update scores
        if result == GameResult.PLAYER1_WIN:
            self.scores["player1"] += 1
            self.statistics["wins"] += 1
            self.statistics["win_streak"] += 1
        elif result == GameResult.PLAYER2_WIN:
            self.scores["player2"] += 1
            self.statistics["losses"] += 1
            self.statistics["win_streak"] = 0
        else:
            self.statistics["draws"] += 1

        # Update best streak
        if self.statistics["win_streak"] > self.statistics["best_streak"]:
            self.statistics["best_streak"] = self.statistics["win_streak"]

        # Record round
        round_data = {
            "round": self.current_round,
            "player1_move": player1_move.name,
            "player2_move": player2_move.name,
            "result": result.value,
            "timestamp": datetime.now().isoformat()
        }

        self.round_history.append(round_data)
        self.current_round += 1

        # Add to move history for pattern analysis
        self.statistics["move_history"].append(player1_move.value)
        if len(self.statistics["move_history"]) > 100:
            self.statistics["move_history"].pop(0)

        return round_data

    def reset_game(self):
        """Reset game state"""
        self.scores = {"player1": 0, "player2": 0}
        self.round_history = []
        self.current_round = 0
        self.statistics["total_games"] += 1
        self.save_statistics()

    def get_ai_move(self) -> Move:
        """Get AI move based on difficulty and pattern analysis"""
        if self.ai_difficulty == "easy":
            return random.choice(list(Move))
        elif self.ai_difficulty == "medium":
            return self._get_strategic_move()
        else:  # hard
            return self._get_predictive_move()

    def _get_strategic_move(self) -> Move:
        """Get strategic AI move based on player patterns"""
        if len(self.statistics["move_history"]) < 5:
            return random.choice(list(Move))

        # Analyze recent moves
        recent_moves = self.statistics["move_history"][-10:]
        move_counts = {1: 0, 2: 0, 3: 0}
        for move in recent_moves:
            move_counts[move] += 1

        # Find most common player move
        most_common = max(move_counts, key=move_counts.get)

        # Counter the most common move
        counter_moves = {1: Move.PAPER, 2: Move.SCISSORS, 3: Move.ROCK}

        # Add some randomness (70% strategic, 30% random)
        if random.random() < 0.7:
            return counter_moves[most_common]
        return random.choice(list(Move))

    def _get_predictive_move(self) -> Move:
        """Use pattern recognition for advanced AI"""
        if len(self.statistics["move_history"]) < 10:
            return self._get_strategic_move()

        # Look for patterns in move sequences
        history = self.statistics["move_history"]
        pattern_length = 3

        if len(history) >= pattern_length:
            recent_pattern = tuple(history[-pattern_length:])

            # Search for this pattern in history
            predictions = []
            for i in range(len(history) - pattern_length - 1):
                if tuple(history[i:i+pattern_length]) == recent_pattern:
                    next_move = history[i + pattern_length]
                    predictions.append(next_move)

            if predictions:
                # Predict the most likely next move
                predicted = max(set(predictions), key=predictions.count)
                counter_moves = {1: Move.PAPER, 2: Move.SCISSORS, 3: Move.ROCK}
                return counter_moves[predicted]

        return self._get_strategic_move()

    def get_leaderboard(self) -> List[Dict]:
        """Get leaderboard data"""
        leaderboard_file = "data/leaderboard.json"
        if os.path.exists(leaderboard_file):
            with open(leaderboard_file, 'r') as f:
                return json.load(f)
        return []

    def update_leaderboard(self, player_name: str, score: int):
        """Update leaderboard with new score"""
        leaderboard = self.get_leaderboard()
        entry = {
            "name": player_name,
            "score": score,
            "date": datetime.now().isoformat(),
            "rounds": self.current_round
        }
        leaderboard.append(entry)
        leaderboard.sort(key=lambda x: x["score"], reverse=True)
        leaderboard = leaderboard[:10]  # Keep top 10

        os.makedirs("data", exist_ok=True)
        with open("data/leaderboard.json", 'w') as f:
            json.dump(leaderboard, f, indent=2)
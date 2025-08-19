"""
Advanced AI player implementation
"""

import random
import numpy as np
from collections import deque
from typing import List, Optional
from src.game_engine import Move

class AIPlayer:
    """AI player with multiple strategies"""

    def __init__(self, difficulty="medium"):
        self.difficulty = difficulty
        self.move_history = deque(maxlen=100)
        self.opponent_history = deque(maxlen=100)
        self.pattern_memory = {}
        self.markov_chain = self._initialize_markov_chain()

    def _initialize_markov_chain(self) -> dict:
        """Initialize Markov chain for move prediction"""
        chain = {}
        for move1 in Move:
            chain[move1] = {}
            for move2 in Move:
                chain[move1][move2] = 1  # Start with uniform distribution
        return chain

    def get_move(self, opponent_history: Optional[List[Move]] = None) -> Move:
        """Get AI move based on difficulty"""
        if self.difficulty == "easy":
            return self._random_move()
        elif self.difficulty == "medium":
            return self._pattern_based_move(opponent_history)
        else:  # hard
            return self._markov_based_move(opponent_history)

    def _random_move(self) -> Move:
        """Simple random move"""
        return random.choice(list(Move))

    def _pattern_based_move(self, opponent_history: Optional[List[Move]]) -> Move:
        """Pattern recognition based move"""
        if not opponent_history or len(opponent_history) < 3:
            return self._random_move()

        # Look for patterns in recent moves
        pattern_length = min(5, len(opponent_history))
        recent_pattern = tuple(opponent_history[-pattern_length:])

        # Check if we've seen this pattern before
        if recent_pattern in self.pattern_memory:
            predicted_move = self.pattern_memory[recent_pattern]
            return self._counter_move(predicted_move)

        # Frequency analysis
        move_counts = {Move.ROCK: 0, Move.PAPER: 0, Move.SCISSORS: 0}
        for move in opponent_history[-10:]:
            move_counts[move] += 1

        # Counter the most frequent move
        most_frequent = max(move_counts, key=move_counts.get)
        return self._counter_move(most_frequent)

    def _markov_based_move(self, opponent_history: Optional[List[Move]]) -> Move:
        """Markov chain based prediction"""
        if not opponent_history or len(opponent_history) < 2:
            return self._pattern_based_move(opponent_history)

        # Update Markov chain
        for i in range(len(opponent_history) - 1):
            current = opponent_history[i]
            next_move = opponent_history[i + 1]
            self.markov_chain[current][next_move] += 1

        # Predict next move based on last move
        last_move = opponent_history[-1]
        predictions = self.markov_chain[last_move]

        # Get most likely next move
        total = sum(predictions.values())
        probabilities = {move: count/total for move, count in predictions.items()}
        predicted = max(probabilities, key=probabilities.get)

        # Add some randomness to avoid being too predictable
        if random.random() < 0.8:  # 80% use prediction
            return self._counter_move(predicted)
        else:
            return self._random_move()

    def _counter_move(self, move: Move) -> Move:
        """Get the counter move"""
        counters = {
            Move.ROCK: Move.PAPER,
            Move.PAPER: Move.SCISSORS,
            Move.SCISSORS: Move.ROCK
        }
        return counters[move]

    def update_history(self, ai_move: Move, opponent_move: Move):
        """Update move history"""
        self.move_history.append(ai_move)
        self.opponent_history.append(opponent_move)

        # Update pattern memory
        if len(self.opponent_history) >= 5:
            pattern = tuple(list(self.opponent_history)[-5:-1])
            self.pattern_memory[pattern] = opponent_move
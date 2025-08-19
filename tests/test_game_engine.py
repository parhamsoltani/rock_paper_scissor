"""
Unit tests for game engine
"""

import unittest
import tempfile
import os
import json
from src.game_engine import GameEngine, Move, GameResult, GameMode

class TestGameEngine(unittest.TestCase):
    """Test cases for GameEngine class"""

    def setUp(self):
        """Set up test environment"""
        self.engine = GameEngine()

        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.original_data_dir = "data"

        # Temporarily redirect data directory
        import src.game_engine
        self.original_stats_file = os.path.join("data", "stats.json")

    def tearDown(self):
        """Clean up test environment"""
        # Clean up temporary files
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_move_enum(self):
        """Test Move enum functionality"""
        # Test move creation
        self.assertEqual(Move.ROCK.value, 1)
        self.assertEqual(Move.PAPER.value, 2)
        self.assertEqual(Move.SCISSORS.value, 3)

        # Test from_fingers method
        self.assertEqual(Move.from_fingers(0), Move.ROCK)
        self.assertEqual(Move.from_fingers(5), Move.PAPER)
        self.assertEqual(Move.from_fingers(2), Move.SCISSORS)
        self.assertIsNone(Move.from_fingers(3))

    def test_move_beats(self):
        """Test move beating logic"""
        # Rock beats Scissors
        self.assertTrue(Move.ROCK.beats(Move.SCISSORS))
        self.assertFalse(Move.SCISSORS.beats(Move.ROCK))

        # Scissors beats Paper
        self.assertTrue(Move.SCISSORS.beats(Move.PAPER))
        self.assertFalse(Move.PAPER.beats(Move.SCISSORS))

        # Paper beats Rock
        self.assertTrue(Move.PAPER.beats(Move.ROCK))
        self.assertFalse(Move.ROCK.beats(Move.PAPER))

        # Same moves don't beat each other
        self.assertFalse(Move.ROCK.beats(Move.ROCK))
        self.assertFalse(Move.PAPER.beats(Move.PAPER))
        self.assertFalse(Move.SCISSORS.beats(Move.SCISSORS))

    def test_determine_winner(self):
        """Test winner determination"""
        # Player 1 wins
        result = self.engine.determine_winner(Move.ROCK, Move.SCISSORS)
        self.assertEqual(result, GameResult.PLAYER1_WIN)

        result = self.engine.determine_winner(Move.PAPER, Move.ROCK)
        self.assertEqual(result, GameResult.PLAYER1_WIN)

        result = self.engine.determine_winner(Move.SCISSORS, Move.PAPER)
        self.assertEqual(result, GameResult.PLAYER1_WIN)

        # Player 2 wins
        result = self.engine.determine_winner(Move.SCISSORS, Move.ROCK)
        self.assertEqual(result, GameResult.PLAYER2_WIN)

        result = self.engine.determine_winner(Move.ROCK, Move.PAPER)
        self.assertEqual(result, GameResult.PLAYER2_WIN)

        result = self.engine.determine_winner(Move.PAPER, Move.SCISSORS)
        self.assertEqual(result, GameResult.PLAYER2_WIN)

        # Draws
        result = self.engine.determine_winner(Move.ROCK, Move.ROCK)
        self.assertEqual(result, GameResult.DRAW)

        result = self.engine.determine_winner(Move.PAPER, Move.PAPER)
        self.assertEqual(result, GameResult.DRAW)

        result = self.engine.determine_winner(Move.SCISSORS, Move.SCISSORS)
        self.assertEqual(result, GameResult.DRAW)

    def test_play_round(self):
        """Test playing a round"""
        initial_scores = self.engine.scores.copy()

        # Play a round where player 1 wins
        result = self.engine.play_round(Move.ROCK, Move.SCISSORS)

        # Check result structure
        self.assertIn('round', result)
        self.assertIn('player1_move', result)
        self.assertIn('player2_move', result)
        self.assertIn('result', result)
        self.assertIn('timestamp', result)

        # Check move recording
        self.assertEqual(result['player1_move'], 'ROCK')
        self.assertEqual(result['player2_move'], 'SCISSORS')
        self.assertEqual(result['result'], 'player1_win')

        # Check score update
        self.assertEqual(self.engine.scores['player1'], initial_scores['player1'] + 1)
        self.assertEqual(self.engine.scores['player2'], initial_scores['player2'])

        # Check round increment
        self.assertEqual(self.engine.current_round, 1)

        # Check history
        self.assertEqual(len(self.engine.round_history), 1)
        self.assertEqual(self.engine.round_history[0], result)

    def test_statistics_update(self):
        """Test statistics updating"""
        initial_stats = self.engine.statistics.copy()

        # Play winning round
        self.engine.play_round(Move.ROCK, Move.SCISSORS)

        # Check statistics
        self.assertEqual(self.engine.statistics['wins'], initial_stats['wins'] + 1)
        self.assertEqual(self.engine.statistics['win_streak'], initial_stats['win_streak'] + 1)

        # Play losing round
        self.engine.play_round(Move.SCISSORS, Move.ROCK)

        # Check statistics
        self.assertEqual(self.engine.statistics['losses'], initial_stats['losses'] + 1)
        self.assertEqual(self.engine.statistics['win_streak'], 0)

        # Play draw round
        self.engine.play_round(Move.ROCK, Move.ROCK)

        # Check statistics
        self.assertEqual(self.engine.statistics['draws'], initial_stats['draws'] + 1)

    def test_ai_moves(self):
        """Test AI move generation"""
        # Test different difficulty levels
        self.engine.ai_difficulty = "easy"
        easy_move = self.engine.get_ai_move()
        self.assertIsInstance(easy_move, Move)

        self.engine.ai_difficulty = "medium"
        medium_move = self.engine.get_ai_move()
        self.assertIsInstance(medium_move, Move)

        self.engine.ai_difficulty = "hard"
        hard_move = self.engine.get_ai_move()
        self.assertIsInstance(hard_move, Move)

    def test_reset_game(self):
        """Test game reset functionality"""
        # Play some rounds
        self.engine.play_round(Move.ROCK, Move.SCISSORS)
        self.engine.play_round(Move.PAPER, Move.ROCK)

        # Verify game state
        self.assertGreater(self.engine.current_round, 0)
        self.assertGreater(len(self.engine.round_history), 0)

        # Reset game
        initial_total_games = self.engine.statistics['total_games']
        self.engine.reset_game()

        # Verify reset
        self.assertEqual(self.engine.scores['player1'], 0)
        self.assertEqual(self.engine.scores['player2'], 0)
        self.assertEqual(self.engine.current_round, 0)
        self.assertEqual(len(self.engine.round_history), 0)
        self.assertEqual(self.engine.statistics['total_games'], initial_total_games + 1)

    def test_pattern_recognition(self):
        """Test AI pattern recognition"""
        # Build pattern in move history
        pattern = [Move.ROCK, Move.PAPER, Move.SCISSORS] * 5
        self.engine.statistics['move_history'] = [move.value for move in pattern]

        # Test strategic move
        self.engine.ai_difficulty = "medium"
        ai_move = self.engine._get_strategic_move()
        self.assertIsInstance(ai_move, Move)

        # Test predictive move
        self.engine.ai_difficulty = "hard"
        ai_move = self.engine._get_predictive_move()
        self.assertIsInstance(ai_move, Move)

    def test_game_modes(self):
        """Test different game modes"""
        # Test mode setting
        self.engine.current_mode = GameMode.VS_AI
        self.assertEqual(self.engine.current_mode, GameMode.VS_AI)

        self.engine.current_mode = GameMode.LOCAL_MULTIPLAYER
        self.assertEqual(self.engine.current_mode, GameMode.LOCAL_MULTIPLAYER)

        self.engine.current_mode = GameMode.ONLINE_MULTIPLAYER
        self.assertEqual(self.engine.current_mode, GameMode.ONLINE_MULTIPLAYER)

    def test_leaderboard(self):
        """Test leaderboard functionality"""
        # Get initial leaderboard
        initial_leaderboard = self.engine.get_leaderboard()
        self.assertIsInstance(initial_leaderboard, list)

        # Update leaderboard
        self.engine.update_leaderboard("TestPlayer", 100)

        # Check leaderboard was updated
        updated_leaderboard = self.engine.get_leaderboard()
        self.assertGreaterEqual(len(updated_leaderboard), len(initial_leaderboard))

class TestMove(unittest.TestCase):
    """Test cases for Move enum"""

    def test_move_values(self):
        """Test move enum values"""
        self.assertEqual(Move.ROCK.value, 1)
        self.assertEqual(Move.PAPER.value, 2)
        self.assertEqual(Move.SCISSORS.value, 3)

    def test_move_names(self):
        """Test move enum names"""
        self.assertEqual(Move.ROCK.name, 'ROCK')
        self.assertEqual(Move.PAPER.name, 'PAPER')
        self.assertEqual(Move.SCISSORS.name, 'SCISSORS')

    def test_move_list(self):
        """Test move enum list"""
        moves = list(Move)
        self.assertEqual(len(moves), 3)
        self.assertIn(Move.ROCK, moves)
        self.assertIn(Move.PAPER, moves)
        self.assertIn(Move.SCISSORS, moves)

if __name__ == '__main__':
    # Create test data directory
    os.makedirs('data', exist_ok=True)

    # Run tests
    unittest.main()
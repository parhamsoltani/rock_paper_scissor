"""
PyQt6-based GUI management
"""

import sys
import json
import cv2
import numpy as np
import time
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from src.game_engine import GameEngine, GameMode, Move
from src.hand_detector import HandDetector
from src.sound_manager import SoundManager
from src.ai_player import AIPlayer

class VideoThread(QThread):
    """Thread for video capture and processing"""

    changePixmap = pyqtSignal(QImage)
    gestureDetected = pyqtSignal(Move)
    noGestureDetected = pyqtSignal()  # New signal for no gesture
    errorOccurred = pyqtSignal(str)

    def __init__(self, camera_index=0):
        super().__init__()
        self.camera_index = camera_index
        self.detector = HandDetector(max_hands=1)
        self.running = False
        self.detect_gesture = False
        self.cap = None
        self.gesture_detected_flag = False
        self.detection_start_time = None
        self.detection_timeout = 3.0  # 3 seconds to make a gesture

    def run(self):
        """Main video capture loop"""
        # Try multiple camera indices if the first one fails
        camera_indices = [0, 1, 2, -1]  # -1 for auto-detection

        for idx in camera_indices:
            try:
                self.cap = cv2.VideoCapture(idx)
                if self.cap.isOpened():
                    # Test if we can actually read from the camera
                    ret, test_frame = self.cap.read()
                    if ret:
                        print(f"Successfully opened camera at index {idx}")
                        break
                    else:
                        self.cap.release()
                        self.cap = None
                else:
                    if self.cap:
                        self.cap.release()
                        self.cap = None
            except Exception as e:
                print(f"Failed to open camera {idx}: {e}")
                if self.cap:
                    self.cap.release()
                    self.cap = None
                continue

        if not self.cap or not self.cap.isOpened():
            self.errorOccurred.emit("No camera found. Please check your camera connection.")
            return

        # Configure camera
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer to avoid lag

        self.running = True
        consecutive_failures = 0
        max_failures = 10

        while self.running:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    consecutive_failures += 1
                    if consecutive_failures >= max_failures:
                        self.errorOccurred.emit("Lost connection to camera")
                        break
                    self.msleep(100)  # Wait before retry
                    continue

                consecutive_failures = 0  # Reset failure counter

                # Flip frame horizontally for mirror effect
                frame = cv2.flip(frame, 1)

                # Detect hands
                frame, hands = self.detector.find_hands(frame, draw=True)

                # Handle gesture detection with timeout
                if self.detect_gesture and not self.gesture_detected_flag:
                    # Initialize detection timer
                    if self.detection_start_time is None:
                        self.detection_start_time = time.time()

                    current_time = time.time()
                    elapsed_time = current_time - self.detection_start_time

                    if hands:
                        hand_info = hands[0]
                        fingers = self.detector.fingers_up(hand_info)
                        gesture = self.detector.recognize_gesture(hand_info)

                        # Draw finger pattern for debugging
                        finger_text = f"Fingers: {fingers} (Total: {sum(fingers)})"
                        cv2.putText(frame, finger_text, (20, 80),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

                        if gesture:
                            print(f"Detected gesture: {gesture.name} with fingers: {fingers}")
                            self.gestureDetected.emit(gesture)
                            self.gesture_detected_flag = True
                            self.detect_gesture = False
                            self.detection_start_time = None
                    else:
                        # Check timeout for no hand detection
                        if elapsed_time >= self.detection_timeout:
                            print("No gesture detected within timeout")
                            self.noGestureDetected.emit()
                            self.gesture_detected_flag = True
                            self.detect_gesture = False
                            self.detection_start_time = None

                # Draw status and instructions
                if self.detect_gesture:
                    if self.detection_start_time:
                        remaining_time = max(0, self.detection_timeout - (time.time() - self.detection_start_time))
                        status_text = f"Make your move! ({remaining_time:.1f}s)"
                    else:
                        status_text = "Make your move!"
                    status_color = (0, 255, 0)

                    # Draw gesture instructions
                    cv2.putText(frame, "Rock: Fist (no fingers)", (20, 120),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                    cv2.putText(frame, "Paper: Open hand (all fingers)", (20, 140),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                    cv2.putText(frame, "Scissors: Peace sign (2 fingers)", (20, 160),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                else:
                    status_text = "Ready - Wait for countdown"
                    status_color = (255, 255, 0)

                cv2.putText(frame, status_text, (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)

                # Convert to Qt format and emit
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line,
                                QImage.Format.Format_RGB888)
                self.changePixmap.emit(qt_image)

            except Exception as e:
                print(f"Error in video thread: {e}")
                consecutive_failures += 1
                if consecutive_failures >= max_failures:
                    self.errorOccurred.emit(f"Camera error: {str(e)}")
                    break

            self.msleep(33)  # ~30 FPS

        # Cleanup
        if self.cap:
            self.cap.release()
            self.cap = None

    def enable_gesture_detection(self):
        """Enable gesture detection for one round"""
        self.detect_gesture = True
        self.gesture_detected_flag = False
        self.detection_start_time = None
        # Reset detector history for fresh detection
        self.detector.reset_history()

    def disable_gesture_detection(self):
        """Disable gesture detection"""
        self.detect_gesture = False
        self.gesture_detected_flag = True
        self.detection_start_time = None

    def stop(self):
        """Stop the video thread"""
        self.running = False
        self.detect_gesture = False
        self.gesture_detected_flag = False
        self.detection_start_time = None

        # Wait for thread to finish
        if not self.wait(3000):  # 3 second timeout
            self.terminate()  # Force terminate if it doesn't stop gracefully
            self.wait(1000)  # Give it another second

        if self.cap:
            self.cap.release()
            self.cap = None

class GameWidget(QWidget):
    """Main game widget"""

    def __init__(self):
        super().__init__()
        self.game_engine = GameEngine()
        self.sound_manager = SoundManager()
        self.ai_player = AIPlayer()
        self.video_thread = None
        self.countdown_timer = QTimer()
        self.countdown_value = 3
        self.game_active = False
        self.round_in_progress = False
        self.player_move_detected = False
        self.waiting_for_gesture = False

        self.init_ui()
        self.start_camera()

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()

        # Title
        title = QLabel("Rock Paper Scissors Game!")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 32px;
                font-weight: bold;
                color: white;
                padding: 20px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3498db, stop:1 #9b59b6);
                border-radius: 10px;
            }
        """)
        layout.addWidget(title)

        # Score display
        self.score_widget = self.create_score_widget()
        layout.addWidget(self.score_widget)

        # Game area
        game_area = QHBoxLayout()

        # Player 1 area
        self.player1_area = self.create_player_area("You")
        game_area.addWidget(self.player1_area)

        # VS indicator
        vs_label = QLabel("VS")
        vs_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vs_label.setStyleSheet("""
            QLabel {
                font-size: 48px;
                font-weight: bold;
                color: #e74c3c;
                padding: 20px;
            }
        """)
        game_area.addWidget(vs_label)

        # Player 2 area
        self.player2_area = self.create_player_area("AI")
        game_area.addWidget(self.player2_area)

        layout.addLayout(game_area)

        # Countdown display
        self.countdown_label = QLabel("")
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.countdown_label.setStyleSheet("""
            QLabel {
                font-size: 72px;
                font-weight: bold;
                color: #e74c3c;
                padding: 20px;
                min-height: 100px;
            }
        """)
        layout.addWidget(self.countdown_label)

        # Control buttons
        controls = self.create_control_buttons()
        layout.addLayout(controls)

        # Statistics panel
        self.stats_panel = self.create_stats_panel()
        layout.addWidget(self.stats_panel)

        self.setLayout(layout)

    def create_score_widget(self) -> QWidget:
        """Create score display widget"""
        widget = QWidget()
        layout = QHBoxLayout()

        self.player1_score = QLabel("0")
        self.player1_score.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.player1_score.setStyleSheet("""
            QLabel {
                font-size: 48px;
                font-weight: bold;
                color: #3498db;
                padding: 10px;
                border: 3px solid #3498db;
                border-radius: 10px;
                min-width: 100px;
            }
        """)

        self.player2_score = QLabel("0")
        self.player2_score.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.player2_score.setStyleSheet("""
            QLabel {
                font-size: 48px;
                font-weight: bold;
                color: #e74c3c;
                padding: 10px;
                border: 3px solid #e74c3c;
                border-radius: 10px;
                min-width: 100px;
            }
        """)

        layout.addWidget(self.player1_score)
        layout.addStretch()
        score_label = QLabel("Score")
        score_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(score_label)
        layout.addStretch()
        layout.addWidget(self.player2_score)

        widget.setLayout(layout)
        return widget

    def create_player_area(self, title: str) -> QWidget:
        """Create player area widget"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title_label)

        # Video/Image display
        display = QLabel()
        display.setFixedSize(320, 240)
        display.setStyleSheet("""
            QLabel {
                border: 2px solid #34495e;
                border-radius: 10px;
                background-color: #ecf0f1;
            }
        """)
        display.setScaledContents(True)
        display.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if title == "You":
            self.player1_display = display
        else:
            self.player2_display = display

        layout.addWidget(display)

        # Gesture display
        gesture_label = QLabel("Ready")
        gesture_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gesture_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #27ae60;
                padding: 10px;
            }
        """)

        if title == "You":
            self.player1_gesture = gesture_label
        else:
            self.player2_gesture = gesture_label

        layout.addWidget(gesture_label)

        widget.setLayout(layout)
        return widget

    def create_control_buttons(self) -> QHBoxLayout:
        """Create control buttons"""
        layout = QHBoxLayout()

        # Start button
        self.start_btn = QPushButton("Start Game")
        self.start_btn.clicked.connect(self.start_game)
        self.start_btn.setStyleSheet("""
            QPushButton {
                font-size: 18px;
                font-weight: bold;
                padding: 15px 30px;
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
            QPushButton:pressed {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)

        # Mode selector
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["VS AI", "Local Multiplayer"])
        self.mode_combo.currentTextChanged.connect(self.change_mode)
        self.mode_combo.setStyleSheet("""
            QComboBox {
                font-size: 16px;
                padding: 10px;
                border: 2px solid #3498db;
                border-radius: 5px;
            }
        """)

        # Difficulty selector
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["Easy", "Medium", "Hard"])
        self.difficulty_combo.setCurrentIndex(1)
        self.difficulty_combo.currentTextChanged.connect(self.change_difficulty)
        self.difficulty_combo.setStyleSheet("""
            QComboBox {
                font-size: 16px;
                padding: 10px;
                border: 2px solid #9b59b6;
                border-radius: 5px;
            }
        """)

        # Reset button
        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self.reset_game)
        reset_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                padding: 10px 20px;
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)

        layout.addWidget(self.start_btn)
        layout.addWidget(self.mode_combo)
        layout.addWidget(self.difficulty_combo)
        layout.addWidget(reset_btn)
        layout.addStretch()

        return layout

    def create_stats_panel(self) -> QWidget:
        """Create statistics panel"""
        widget = QWidget()
        layout = QHBoxLayout()

        # Win rate
        self.win_rate_label = QLabel("Win Rate: 0%")
        self.win_rate_label.setStyleSheet("font-size: 14px; color: #2c3e50;")

        # Streak
        self.streak_label = QLabel("Current Streak: 0")
        self.streak_label.setStyleSheet("font-size: 14px; color: #2c3e50;")

        # Total games
        self.total_games_label = QLabel("Total Games: 0")
        self.total_games_label.setStyleSheet("font-size: 14px; color: #2c3e50;")

        layout.addWidget(self.win_rate_label)
        layout.addWidget(self.streak_label)
        layout.addWidget(self.total_games_label)
        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def start_camera(self):
        """Initialize camera"""
        if not self.video_thread:
            self.video_thread = VideoThread()
            self.video_thread.changePixmap.connect(self.update_player1_display)
            self.video_thread.gestureDetected.connect(self.on_gesture_detected)
            self.video_thread.noGestureDetected.connect(self.on_no_gesture_detected)
            self.video_thread.errorOccurred.connect(self.on_camera_error)
            self.video_thread.start()

    def on_camera_error(self, error_message):
        """Handle camera errors"""
        print(f"Camera error: {error_message}")
        QMessageBox.warning(self, "Camera Error", error_message)
        self.player1_display.setText("Camera\nNot Available\n\nClick Start Game\nto use manual input")
        self.player1_display.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #e74c3c;
                border: 2px solid #e74c3c;
                border-radius: 10px;
                background-color: #ecf0f1;
            }
        """)

    def start_game(self):
        """Start a new game with proper timing"""
        if self.round_in_progress:
            return

        self.sound_manager.play_sound("click")
        self.round_in_progress = True
        self.player_move_detected = False
        self.waiting_for_gesture = False

        # Reset displays
        self.player1_gesture.setText("Get Ready...")
        self.player2_gesture.setText("Get Ready...")
        self.countdown_label.setText("")

        # Ensure gesture detection is disabled during countdown
        if self.video_thread:
            self.video_thread.disable_gesture_detection()

        # Start countdown
        self.countdown_value = 3
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_timer.start(1000)

        self.start_btn.setEnabled(False)
        self.mode_combo.setEnabled(False)
        self.difficulty_combo.setEnabled(False)

    def update_countdown(self):
        """Update countdown display with proper timing"""
        if self.countdown_value > 0:
            self.countdown_label.setText(str(self.countdown_value))
            self.sound_manager.play_sound("countdown")
            self.countdown_value -= 1
        else:
            self.countdown_timer.stop()
            self.countdown_timer.timeout.disconnect()
            self.countdown_label.setText("SHOOT!")

            # NOW enable gesture detection after countdown
            self.waiting_for_gesture = True
            if self.video_thread:
                self.video_thread.enable_gesture_detection()

    def on_gesture_detected(self, gesture: Move):
        """Handle detected gesture"""
        if not self.round_in_progress or self.player_move_detected or not self.waiting_for_gesture:
            return

        self.player_move_detected = True
        self.waiting_for_gesture = False

        # Disable further gesture detection
        if self.video_thread:
            self.video_thread.disable_gesture_detection()

        self._process_round(gesture)

    def on_no_gesture_detected(self):
        """Handle case when no gesture is detected within timeout"""
        if not self.round_in_progress or self.player_move_detected or not self.waiting_for_gesture:
            return

        self.player_move_detected = True
        self.waiting_for_gesture = False

        # Check if camera is working
        if not self.video_thread or not self.video_thread.cap:
            self.show_manual_input_dialog()
        else:
            # Show "No gesture detected" message
            self.show_no_gesture_message()

    def show_no_gesture_message(self):
        """Show message when no gesture is detected"""
        self.player1_gesture.setText("No gesture detected")
        self.player1_gesture.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #e74c3c;
                padding: 10px;
            }
        """)

        self.countdown_label.setText("No move detected!")
        self.countdown_label.setStyleSheet("""
            QLabel {
                font-size: 36px;
                font-weight: bold;
                color: #e74c3c;
                padding: 20px;
                min-height: 100px;
            }
        """)

        # Wait a moment then reset
        QTimer.singleShot(2000, self.reset_round)

    def show_manual_input_dialog(self):
        """Show manual input dialog when camera is not available"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Make Your Move")
        dialog.setModal(True)
        layout = QVBoxLayout()

        label = QLabel("Camera not available. Choose your move:")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        button_layout = QHBoxLayout()

        rock_btn = QPushButton("✊ Rock")
        rock_btn.clicked.connect(lambda: self.manual_move_selected(Move.ROCK, dialog))

        paper_btn = QPushButton("✋ Paper")
        paper_btn.clicked.connect(lambda: self.manual_move_selected(Move.PAPER, dialog))

        scissors_btn = QPushButton("✌️ Scissors")
        scissors_btn.clicked.connect(lambda: self.manual_move_selected(Move.SCISSORS, dialog))

        for btn in [rock_btn, paper_btn, scissors_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 16px;
                    padding: 10px 20px;
                    margin: 5px;
                    border-radius: 5px;
                    background-color: #3498db;
                    color: white;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """)

        button_layout.addWidget(rock_btn)
        button_layout.addWidget(paper_btn)
        button_layout.addWidget(scissors_btn)

        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        dialog.exec()

    def manual_move_selected(self, move: Move, dialog: QDialog):
        """Handle manual move selection"""
        dialog.close()
        self._process_round(move)

    def _process_round(self, player_move: Move):
        """Process the round with given player move"""
        # Show player move
        self.player1_gesture.setText(player_move.name)
        self.player1_gesture.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #3498db;
                padding: 10px;
            }
        """)

        # Generate AI move
        ai_move = self.game_engine.get_ai_move()
        self.player2_gesture.setText(ai_move.name)
        self.player2_gesture.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #e74c3c;
                padding: 10px;
            }
        """)

        # Show AI move visualization
        self.show_move_image(self.player2_display, ai_move)

        # Process round
        result = self.game_engine.play_round(player_move, ai_move)

        # Update scores
        self.update_scores()

        # Show result and play sound
        if result["result"] == "player1_win":
            self.sound_manager.play_sound("win")
            self.show_result("You Win!", "#27ae60")
        elif result["result"] == "player2_win":
            self.sound_manager.play_sound("lose")
            self.show_result("You Lose!", "#e74c3c")
        else:
            self.sound_manager.play_sound("draw")
            self.show_result("Draw!", "#f39c12")

        # Update statistics
        self.update_statistics()

        # Schedule round reset
        QTimer.singleShot(3000, self.reset_round)

    def show_move_image(self, display: QLabel, move: Move):
        """Show move as text emoji"""
        move_symbols = {
            Move.ROCK: "✊",
            Move.PAPER: "✋",
            Move.SCISSORS: "✌️"
        }

        display.setText(move_symbols.get(move, "❓"))
        display.setStyleSheet("""
            QLabel {
                font-size: 48px;
                color: #2c3e50;
                border: 2px solid #34495e;
                border-radius: 10px;
                background-color: #ecf0f1;
            }
        """)

    def show_result(self, text: str, color: str):
        """Show round result"""
        self.countdown_label.setText(text)
        self.countdown_label.setStyleSheet(f"""
            QLabel {{
                font-size: 48px;
                font-weight: bold;
                color: {color};
                padding: 20px;
                min-height: 100px;
            }}
        """)

    def reset_round(self):
        """Reset for next round"""
        self.round_in_progress = False
        self.player_move_detected = False
        self.waiting_for_gesture = False

        # Re-enable controls
        self.start_btn.setEnabled(True)
        self.mode_combo.setEnabled(True)
        self.difficulty_combo.setEnabled(True)

        # Reset displays
        self.countdown_label.setText("")
        self.countdown_label.setStyleSheet("""
            QLabel {
                font-size: 72px;
                font-weight: bold;
                color: #e74c3c;
                padding: 20px;
                min-height: 100px;
            }
        """)

        self.player1_gesture.setText("Ready")
        self.player1_gesture.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #27ae60;
                padding: 10px;
            }
        """)

        self.player2_gesture.setText("Ready")
        self.player2_gesture.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #27ae60;
                padding: 10px;
            }
        """)

        # Reset AI display
        self.player2_display.setText("")
        self.player2_display.setStyleSheet("""
            QLabel {
                border: 2px solid #34495e;
                border-radius: 10px;
                background-color: #ecf0f1;
            }
        """)

        # Ensure gesture detection is disabled
        if self.video_thread:
            self.video_thread.disable_gesture_detection()

    def update_player1_display(self, image: QImage):
        """Update player 1 video display"""
        self.player1_display.setPixmap(QPixmap.fromImage(image))

    def update_scores(self):
        """Update score display"""
        self.player1_score.setText(str(self.game_engine.scores["player1"]))
        self.player2_score.setText(str(self.game_engine.scores["player2"]))

    def update_statistics(self):
        """Update statistics display"""
        stats = self.game_engine.statistics
        total = stats["wins"] + stats["losses"] + stats["draws"]
        if total > 0:
            win_rate = (stats["wins"] / total) * 100
            self.win_rate_label.setText(f"Win Rate: {win_rate:.1f}%")

        self.streak_label.setText(f"Current Streak: {stats['win_streak']}")
        self.total_games_label.setText(f"Total Games: {stats['total_games']}")

    def change_mode(self, mode: str):
        """Change game mode"""
        mode_map = {
            "VS AI": GameMode.VS_AI,
            "Local Multiplayer": GameMode.LOCAL_MULTIPLAYER
        }
        self.game_engine.current_mode = mode_map.get(mode, GameMode.VS_AI)

    def change_difficulty(self, difficulty: str):
        """Change AI difficulty"""
        self.game_engine.ai_difficulty = difficulty.lower()

    def reset_game(self):
        """Reset the game"""
        # Stop any ongoing round
        if self.countdown_timer.isActive():
            self.countdown_timer.stop()

        self.round_in_progress = False
        self.player_move_detected = False
        self.waiting_for_gesture = False

        # Reset game engine
        self.game_engine.reset_game()

        # Update displays
        self.update_scores()
        self.update_statistics()

        # Reset UI
        self.reset_round()

        self.sound_manager.play_sound("click")

    def closeEvent(self, event):
        """Handle widget close event"""
        if self.video_thread:
            self.video_thread.stop()
        self.game_engine.save_statistics()
        event.accept()

class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rock Paper Scissors Advanced")
        self.setGeometry(100, 100, 1200, 800)

        # Create central widget
        self.game_widget = GameWidget()
        self.setCentralWidget(self.game_widget)

        # Create menu bar
        self.create_menu_bar()

        # Apply stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ecf0f1;
            }
        """)

    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        new_game = QAction("New Game", self)
        new_game.setShortcut("Ctrl+N")
        new_game.triggered.connect(self.game_widget.reset_game)
        file_menu.addAction(new_game)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("View")

        stats_action = QAction("Statistics", self)
        stats_action.triggered.connect(self.show_statistics)
        view_menu.addAction(stats_action)

        # Settings menu
        settings_menu = menubar.addMenu("Settings")

        sound_action = QAction("Toggle Sound", self)
        sound_action.setCheckable(True)
        sound_action.setChecked(True)
        sound_action.triggered.connect(self.toggle_sound)
        settings_menu.addAction(sound_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def show_statistics(self):
        """Show statistics dialog"""
        stats = self.game_widget.game_engine.statistics

        dialog = QDialog(self)
        dialog.setWindowTitle("Game Statistics")
        dialog.setModal(True)
        dialog.resize(400, 300)

        layout = QVBoxLayout()

        stats_text = f"""
        <h2>Your Statistics</h2>
        <p><b>Total Games:</b> {stats['total_games']}</p>
        <p><b>Wins:</b> {stats['wins']}</p>
        <p><b>Losses:</b> {stats['losses']}</p>
        <p><b>Draws:</b> {stats['draws']}</p>
        <p><b>Best Win Streak:</b> {stats['best_streak']}</p>
        <p><b>Current Streak:</b> {stats['win_streak']}</p>
        """

        label = QLabel(stats_text)
        label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(label)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)

        dialog.setLayout(layout)
        dialog.exec()

    def toggle_sound(self, checked):
        """Toggle sound on/off"""
        self.game_widget.sound_manager.enabled = checked

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About",
            """<h2>Rock Paper Scissors Advanced</h2>
            <p>Version 2.0</p>
            <p>An advanced implementation of the classic game with AI opponents,
            gesture recognition, and multiplayer support.</p>
            <p>Created with Python, OpenCV, MediaPipe, and PyQt6</p>""")

    def closeEvent(self, event):
        """Handle window close event"""
        if self.game_widget.video_thread:
            self.game_widget.video_thread.stop()
        self.game_widget.game_engine.save_statistics()
        event.accept()
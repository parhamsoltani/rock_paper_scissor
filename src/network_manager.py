"""
Network management for multiplayer functionality
"""

import socket
import threading
import json
import time
import logging
from typing import Dict, Any, Optional, Callable
from PyQt6.QtCore import QObject, pyqtSignal
from src.game_engine import Move
from src.utils import generate_session_id

class NetworkManager(QObject):
    """Handle network communications for multiplayer"""

    # Signals for GUI updates
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    message_received = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.socket = None
        self.is_host = False
        self.is_connected = False
        self.session_id = generate_session_id()
        self.player_name = "Player"
        self.opponent_name = "Opponent"
        self.receive_thread = None
        self.logger = logging.getLogger(__name__)

        # Message handlers
        self.message_handlers = {
            "move": self._handle_move_message,
            "ready": self._handle_ready_message,
            "disconnect": self._handle_disconnect_message,
            "chat": self._handle_chat_message,
            "game_state": self._handle_game_state_message
        }

    def host_game(self, port: int = 5555) -> bool:
        """Host a multiplayer game"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('', port))
            self.socket.listen(1)

            self.is_host = True
            self.logger.info(f"Hosting game on port {port}")

            # Wait for connection in separate thread
            threading.Thread(target=self._wait_for_connection, daemon=True).start()
            return True

        except Exception as e:
            self.logger.error(f"Failed to host game: {e}")
            self.error_occurred.emit(f"Failed to host game: {e}")
            return False

    def join_game(self, host_ip: str, port: int = 5555) -> bool:
        """Join a multiplayer game"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)  # 10 second timeout
            self.socket.connect((host_ip, port))

            self.is_host = False
            self.is_connected = True
            self.logger.info(f"Connected to {host_ip}:{port}")

            # Start receiving messages
            self._start_receive_thread()
            self.connected.emit()

            # Send initial handshake
            self.send_message("handshake", {
                "player_name": self.player_name,
                "session_id": self.session_id
            })

            return True

        except Exception as e:
            self.logger.error(f"Failed to join game: {e}")
            self.error_occurred.emit(f"Failed to join game: {e}")
            return False

    def _wait_for_connection(self):
        """Wait for incoming connection (host only)"""
        try:
            client_socket, address = self.socket.accept()
            self.socket = client_socket
            self.is_connected = True

            self.logger.info(f"Client connected from {address}")
            self._start_receive_thread()
            self.connected.emit()

        except Exception as e:
            self.logger.error(f"Error accepting connection: {e}")
            self.error_occurred.emit(f"Connection error: {e}")

    def _start_receive_thread(self):
        """Start thread to receive messages"""
        self.receive_thread = threading.Thread(target=self._receive_messages, daemon=True)
        self.receive_thread.start()

    def _receive_messages(self):
        """Receive and process incoming messages"""
        while self.is_connected:
            try:
                data = self.socket.recv(1024)
                if not data:
                    break

                message = json.loads(data.decode('utf-8'))
                self.message_received.emit(message)

                # Handle message based on type
                msg_type = message.get('type')
                if msg_type in self.message_handlers:
                    self.message_handlers[msg_type](message)

            except (ConnectionResetError, json.JSONDecodeError) as e:
                self.logger.error(f"Receive error: {e}")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in receive: {e}")
                break

        self._handle_disconnection()

    def send_message(self, msg_type: str, data: Dict[str, Any]) -> bool:
        """Send message to opponent"""
        if not self.is_connected or not self.socket:
            return False

        try:
            message = {
                "type": msg_type,
                "timestamp": time.time(),
                "session_id": self.session_id,
                "data": data
            }

            json_data = json.dumps(message).encode('utf-8')
            self.socket.send(json_data)
            return True

        except Exception as e:
            self.logger.error(f"Send error: {e}")
            self.error_occurred.emit(f"Failed to send message: {e}")
            return False

    def send_move(self, move: Move) -> bool:
        """Send player move"""
        return self.send_message("move", {
            "move": move.name,
            "player": self.player_name
        })

    def send_ready_signal(self) -> bool:
        """Send ready signal"""
        return self.send_message("ready", {
            "player": self.player_name
        })

    def send_chat_message(self, message: str) -> bool:
        """Send chat message"""
        return self.send_message("chat", {
            "player": self.player_name,
            "message": message
        })

    def send_game_state(self, game_state: Dict[str, Any]) -> bool:
        """Send current game state"""
        return self.send_message("game_state", game_state)

    def _handle_move_message(self, message: Dict[str, Any]):
        """Handle received move message"""
        data = message.get('data', {})
        move_name = data.get('move')
        player = data.get('player')

        if move_name:
            try:
                move = Move[move_name]
                self.logger.info(f"Received move {move_name} from {player}")
                # Emit signal for game engine to process
            except KeyError:
                self.logger.error(f"Invalid move received: {move_name}")

    def _handle_ready_message(self, message: Dict[str, Any]):
        """Handle ready signal"""
        data = message.get('data', {})
        player = data.get('player')
        self.logger.info(f"Player {player} is ready")

    def _handle_disconnect_message(self, message: Dict[str, Any]):
        """Handle disconnect message"""
        self._handle_disconnection()

    def _handle_chat_message(self, message: Dict[str, Any]):
        """Handle chat message"""
        data = message.get('data', {})
        player = data.get('player')
        chat_msg = data.get('message')
        self.logger.info(f"Chat from {player}: {chat_msg}")

    def _handle_game_state_message(self, message: Dict[str, Any]):
        """Handle game state update"""
        data = message.get('data', {})
        self.logger.info("Received game state update")

    def _handle_disconnection(self):
        """Handle connection loss"""
        if self.is_connected:
            self.is_connected = False
            self.disconnected.emit()
            self.logger.info("Disconnected from opponent")

    def disconnect(self):
        """Disconnect from opponent"""
        if self.is_connected:
            self.send_message("disconnect", {"player": self.player_name})
            time.sleep(0.1)  # Give time for message to send

        self.is_connected = False

        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None

        self.logger.info("Disconnected")

    def get_local_ip(self) -> str:
        """Get local IP address"""
        try:
            # Create a socket to determine local IP
            temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            temp_socket.connect(("8.8.8.8", 80))
            local_ip = temp_socket.getsockname()[0]
            temp_socket.close()
            return local_ip
        except:
            return "127.0.0.1"

    def set_player_name(self, name: str):
        """Set player name"""
        self.player_name = name

    def set_opponent_name(self, name: str):
        """Set opponent name"""
        self.opponent_name = name

class NetworkGameState:
    """Manage synchronized game state across network"""

    def __init__(self, network_manager: NetworkManager):
        self.network = network_manager
        self.local_ready = False
        self.remote_ready = False
        self.local_move = None
        self.remote_move = None
        self.round_number = 0

    def set_local_ready(self, ready: bool):
        """Set local player ready state"""
        self.local_ready = ready
        if ready:
            self.network.send_ready_signal()

    def set_local_move(self, move: Move):
        """Set local player move"""
        self.local_move = move
        self.network.send_move(move)

    def both_ready(self) -> bool:
        """Check if both players are ready"""
        return self.local_ready and self.remote_ready

    def both_moved(self) -> bool:
        """Check if both players have made moves"""
        return self.local_move is not None and self.remote_move is not None

    def reset_round(self):
        """Reset for new round"""
        self.local_ready = False
        self.remote_ready = False
        self.local_move = None
        self.remote_move = None
        self.round_number += 1

    def get_moves(self) -> tuple:
        """Get both player moves"""
        return self.local_move, self.remote_move
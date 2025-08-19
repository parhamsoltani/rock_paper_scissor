"""
MediaPipe-based hand detection and gesture recognition
"""

import cv2
import mediapipe as mp
import numpy as np
from typing import Optional, List, Tuple
from src.game_engine import Move

class HandDetector:
    """Advanced hand detection with MediaPipe"""

    def __init__(self, mode=False, max_hands=1, detection_confidence=0.7,
                 tracking_confidence=0.5):
        self.mode = mode
        self.max_hands = max_hands
        self.detection_con = detection_confidence
        self.tracking_con = tracking_confidence

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.max_hands,
            min_detection_confidence=self.detection_con,
            min_tracking_confidence=self.tracking_con
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.tip_ids = [4, 8, 12, 16, 20]

        # Gesture recognition parameters
        self.gesture_history = []
        self.gesture_threshold = 5  # Increased for better stability
        self.confidence_threshold = 3  # Minimum confidence for gesture detection

    def find_hands(self, img, draw=True):
        """Find hands in the image"""
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(img_rgb)

        all_hands = []
        if self.results.multi_hand_landmarks:
            for hand_idx, hand_lms in enumerate(self.results.multi_hand_landmarks):
                if draw:
                    self.mp_draw.draw_landmarks(
                        img, hand_lms, self.mp_hands.HAND_CONNECTIONS,
                        self.mp_draw.DrawingSpec(color=(0, 255, 0), thickness=2),
                        self.mp_draw.DrawingSpec(color=(255, 0, 0), thickness=2)
                    )

                # Get hand info
                hand_info = self._get_hand_info(hand_lms, img)
                all_hands.append(hand_info)

        return img, all_hands

    def _get_hand_info(self, hand_lms, img) -> dict:
        """Extract hand information"""
        h, w, c = img.shape
        lm_list = []
        x_list = []
        y_list = []

        for id, lm in enumerate(hand_lms.landmark):
            cx, cy = int(lm.x * w), int(lm.y * h)
            lm_list.append([id, cx, cy])
            x_list.append(cx)
            y_list.append(cy)

        # Calculate bounding box
        bbox = (min(x_list), min(y_list), max(x_list), max(y_list))

        return {
            "lmList": lm_list,
            "bbox": bbox,
            "center": ((bbox[0] + bbox[2]) // 2, (bbox[1] + bbox[3]) // 2)
        }

    def fingers_up(self, hand_info: dict) -> List[int]:
        """Count fingers that are up - improved logic"""
        fingers = []
        lm_list = hand_info["lmList"]

        if len(lm_list) < 21:
            return [0, 0, 0, 0, 0]

        # Thumb - improved detection
        # Check if thumb tip is significantly away from other fingers
        thumb_tip = lm_list[4]
        thumb_ip = lm_list[3]
        index_mcp = lm_list[5]

        # Calculate distance between thumb tip and index finger base
        thumb_distance = abs(thumb_tip[1] - index_mcp[1])

        # Thumb is up if it's far enough from index finger and above IP joint
        if thumb_distance > 30 and thumb_tip[2] < thumb_ip[2]:
            fingers.append(1)
        else:
            fingers.append(0)

        # Four fingers - improved detection with more strict criteria
        for id in range(1, 5):
            tip_y = lm_list[self.tip_ids[id]][2]
            pip_y = lm_list[self.tip_ids[id] - 2][2]
            mcp_y = lm_list[self.tip_ids[id] - 3][2]

            # Finger is up if tip is significantly above PIP and PIP is above MCP
            if tip_y < pip_y - 10 and pip_y < mcp_y:
                fingers.append(1)
            else:
                fingers.append(0)

        return fingers

    def recognize_gesture(self, hand_info: dict) -> Optional[Move]:
        """Recognize rock, paper, scissors gesture with improved accuracy"""
        fingers = self.fingers_up(hand_info)

        # Determine gesture based on finger pattern
        gesture = None

        # Count total fingers up
        total_fingers = sum(fingers)

        # Rock: No fingers or only thumb (fist)
        if total_fingers == 0:
            gesture = Move.ROCK
        # Paper: 4 or 5 fingers up (open hand)
        elif total_fingers >= 4:
            gesture = Move.PAPER
        # Scissors: Exactly 2 fingers (index and middle)
        elif total_fingers == 2 and fingers[1] == 1 and fingers[2] == 1:
            gesture = Move.SCISSORS
        # Alternative scissors: 3 fingers (thumb, index, middle)
        elif total_fingers == 3 and fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 1:
            gesture = Move.SCISSORS

        # Add to history for stability
        self.gesture_history.append(gesture)
        if len(self.gesture_history) > self.gesture_threshold:
            self.gesture_history.pop(0)

        # Return gesture only if stable and confident
        if len(self.gesture_history) >= self.gesture_threshold:
            # Count occurrences of each gesture (excluding None)
            gesture_counts = {}
            for g in self.gesture_history:
                if g is not None:
                    gesture_counts[g] = gesture_counts.get(g, 0) + 1

            if gesture_counts:
                # Return the most frequent gesture if it meets confidence threshold
                most_frequent = max(gesture_counts, key=gesture_counts.get)
                if gesture_counts[most_frequent] >= self.confidence_threshold:
                    return most_frequent

        return None

    def has_hand_detected(self) -> bool:
        """Check if any hand is currently detected"""
        return self.results is not None and self.results.multi_hand_landmarks is not None

    def draw_gesture_feedback(self, img, gesture: Optional[Move], fingers: List[int],
                             position: Tuple[int, int]):
        """Draw gesture feedback on image with finger info"""
        if gesture:
            text = gesture.name
            color = (0, 255, 0)
        else:
            if self.has_hand_detected():
                text = "Position your hand"
                color = (255, 255, 0)
            else:
                text = "No hand detected"
                color = (255, 0, 0)

        # Draw main gesture text
        cv2.putText(img, text, position, cv2.FONT_HERSHEY_SIMPLEX,
                   1, color, 2, cv2.LINE_AA)

        # Draw finger pattern for debugging
        if fingers and any(f > 0 for f in fingers):
            finger_text = f"Fingers: {fingers} (Total: {sum(fingers)})"
            cv2.putText(img, finger_text, (position[0], position[1] + 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

        return img

    def reset_history(self):
        """Reset gesture history"""
        self.gesture_history = []
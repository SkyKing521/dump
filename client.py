import asyncio
import json
import websockets
import aiortc
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate
from aiortc.contrib.media import MediaStreamTrack, MediaRecorder
import cv2
import numpy as np
from av import VideoFrame
import sys
import logging
import os
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QPushButton, QFrame, QScrollArea, QLineEdit, QMessageBox,
                           QFileDialog, QMenu, QSystemTrayIcon, QDialog, QFormLayout, QCheckBox, QTextEdit)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QFont, QImage, QPixmap, QAction
import time
import requests
from login_dialog import LoginDialog
from init_db import User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash
from main_menu import MainMenu
from video_chat_window import MainWindow
from config import WEBSOCKET_SERVER, DATABASE_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# STUN/TURN configuration
RTC_CONFIGURATION = {
    "iceServers": [
        {
            "urls": [
                "stun:stun.l.google.com:19302",
                "stun:stun1.l.google.com:19302",
                "stun:stun2.l.google.com:19302",
                "stun:stun3.l.google.com:19302",
                "stun:stun4.l.google.com:19302"
            ]
        }
    ]
}

class VideoStreamTrack(MediaStreamTrack):
    kind = "video"

    def __init__(self):
        super().__init__()
        self.muted = False
        self.cap = None
        self.frame_width = 640
        self.frame_height = 480
        self.frame_rate = 30
        self.last_frame_time = 0
        self.start_video_capture()

    def start_video_capture(self):
        try:
            # Try different camera indices
            for i in range(3):  # Try first 3 camera indices
                self.cap = cv2.VideoCapture(i)
                if self.cap.isOpened():
                    logger.info(f"Successfully opened camera with index {i}")
                    break
                else:
                    self.cap.release()
            
            if not self.cap or not self.cap.isOpened():
                raise Exception("Failed to open any camera device")
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            self.cap.set(cv2.CAP_PROP_FPS, self.frame_rate)
            
            # Verify settings
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
            
            if actual_width != self.frame_width or actual_height != self.frame_height:
                logger.warning(f"Camera resolution set to {actual_width}x{actual_height} instead of {self.frame_width}x{self.frame_height}")
            
            if actual_fps != self.frame_rate:
                logger.warning(f"Camera FPS set to {actual_fps} instead of {self.frame_rate}")
                
        except Exception as e:
            logger.error(f"Failed to start video capture: {e}")
            self.cap = None

    async def recv(self):
        if self.muted or not self.cap:
            return None

        try:
            ret, frame = self.cap.read()
            if not ret:
                logger.error("Failed to read frame from camera")
                # Try to restart camera
                self.cap.release()
                self.start_video_capture()
                return None

            # Control frame rate
            current_time = time.time()
            if current_time - self.last_frame_time < 1.0 / self.frame_rate:
                await asyncio.sleep(0.01)
                return None
            self.last_frame_time = current_time

            # Convert frame to RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Create video frame
            video_frame = VideoFrame.from_ndarray(frame, format='rgb24')
            return video_frame

        except Exception as e:
            logger.error(f"Error processing video frame: {e}")
            return None

    def stop(self):
        if self.cap:
            self.cap.release()
        super().stop()

    def set_muted(self, muted):
        self.muted = muted

class AudioStreamTrack(MediaStreamTrack):
    kind = "audio"

    def __init__(self):
        super().__init__()
        self.muted = False
        self.sample_rate = 48000
        self.channels = 1
        self.sample_width = 2  # 16-bit audio
        self.stream = None
        self.output_stream = None  # For self-monitoring
        self.audio_buffer = []
        self.buffer_size = 1024
        self.start_audio_capture()

    def start_audio_capture(self):
        import sounddevice as sd
        import numpy as np
        
        def audio_callback(indata, frames, time, status):
            if status:
                logger.warning(f"Audio capture status: {status}")
            if not self.muted:
                # Store audio data for WebRTC
                self.audio_buffer.extend(indata[:, 0])  # Take first channel if stereo
                # Play audio for self-monitoring
                if self.output_stream:
                    self.output_stream.write(indata)

        try:
            # Input stream for capturing
            self.stream = sd.InputStream(
                channels=self.channels,
                samplerate=self.sample_rate,
                callback=audio_callback,
                blocksize=self.buffer_size,
                dtype=np.float32
            )
            
            # Output stream for self-monitoring
            self.output_stream = sd.OutputStream(
                channels=self.channels,
                samplerate=self.sample_rate,
                blocksize=self.buffer_size,
                dtype=np.float32
            )
            
            self.stream.start()
            self.output_stream.start()
            
        except Exception as e:
            logger.error(f"Failed to start audio capture: {e}")
            self.stream = None
            self.output_stream = None

    async def recv(self):
        if self.muted or not self.stream:
            return None

        import numpy as np
        from av import AudioFrame

        if len(self.audio_buffer) < self.buffer_size:
            await asyncio.sleep(0.01)  # Wait for more audio data
            return None

        # Get audio data from buffer
        audio_data = np.array(self.audio_buffer[:self.buffer_size], dtype=np.float32)
        self.audio_buffer = self.audio_buffer[self.buffer_size:]

        # Convert to 16-bit PCM
        audio_data = (audio_data * 32767).astype(np.int16)

        # Create audio frame
        frame = AudioFrame.from_ndarray(audio_data, layout='mono', rate=self.sample_rate)
        return frame

    def stop(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
        if self.output_stream:
            self.output_stream.stop()
            self.output_stream.close()
        super().stop()

    def set_muted(self, muted):
        self.muted = muted

class WebRTCClient(QThread):
    video_received = pyqtSignal(int, QImage)
    user_joined = pyqtSignal(int, str)
    user_left = pyqtSignal(int)
    recording_status = pyqtSignal(bool)
    connection_status = pyqtSignal(bool)
    message_received = pyqtSignal(str, str)
    error_occurred = pyqtSignal(str)  # New signal for error reporting

    def __init__(self, room_id, display_name, server_url):
        super().__init__()
        self.room_id = room_id
        self.display_name = display_name
        self.server_url = server_url
        self.peer_connections = {}
        self.video_track = VideoStreamTrack()
        self.audio_track = AudioStreamTrack()
        self.websocket = None
        self.running = True
        self.recorder = None
        self.is_recording = False
        self.data_channels = {}
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 2  # seconds

    async def connect(self):
        try:
            if self.websocket is not None:
                await self.websocket.close()
                self.websocket = None

            self.websocket = await websockets.connect(
                self.server_url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=5
            )
            
            await self.websocket.send(json.dumps({
                'type': 'join',
                'room_id': self.room_id,
                'name': self.display_name
            }))
            
            self.connection_status.emit(True)
            self.reconnect_attempts = 0
            logger.info("Successfully connected to signaling server")
            
        except Exception as e:
            logger.error(f"Connection error: {e}")
            self.connection_status.emit(False)
            self.error_occurred.emit(f"Connection error: {str(e)}")
            raise

    def start_recording(self, output_file):
        if not self.is_recording:
            self.recorder = MediaRecorder(output_file)
            self.recorder.addTrack(self.video_track)
            self.recorder.addTrack(self.audio_track)
            asyncio.run(self.recorder.start())
            self.is_recording = True
            self.recording_status.emit(True)

    def stop_recording(self):
        if self.is_recording and self.recorder:
            asyncio.run(self.recorder.stop())
            self.is_recording = False
            self.recording_status.emit(False)

    async def handle_signaling(self):
        while self.running:
            try:
                if self.websocket is None or self.websocket.closed:
                    if self.reconnect_attempts < self.max_reconnect_attempts:
                        self.reconnect_attempts += 1
                        logger.info(f"Attempting to reconnect (attempt {self.reconnect_attempts})...")
                        await asyncio.sleep(self.reconnect_delay)
                        await self.connect()
                        continue
                    else:
                        logger.error("Max reconnection attempts reached")
                        self.error_occurred.emit("Failed to connect to server after multiple attempts")
                        break

                message = await self.websocket.recv()
                data = json.loads(message)
                
                if data['type'] == 'user-list':
                    await self.handle_user_list(data)
                elif data['type'] == 'user-joined':
                    self.user_joined.emit(data['user_id'], data['name'])
                elif data['type'] == 'user-left':
                    self.user_left.emit(data['user_id'])
                    await self.handle_user_left(data['user_id'])
                elif data['type'] == 'offer':
                    await self.handle_offer(data)
                elif data['type'] == 'answer':
                    await self.handle_answer(data)
                elif data['type'] == 'ice-candidate':
                    await self.handle_ice_candidate(data)
                    
            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed")
                self.connection_status.emit(False)
                if self.running:
                    await asyncio.sleep(self.reconnect_delay)
                    continue
            except Exception as e:
                logger.error(f"Error handling signaling: {e}")
                self.error_occurred.emit(f"Signaling error: {str(e)}")
                if self.running:
                    await asyncio.sleep(self.reconnect_delay)
                    continue

    async def handle_user_list(self, data):
        for user in data['users']:
            await self.create_peer_connection(user['id'])

    async def handle_user_left(self, user_id):
        if user_id in self.peer_connections:
            await self.peer_connections[user_id].close()
            del self.peer_connections[user_id]

    async def create_peer_connection(self, peer_id):
        if peer_id in self.peer_connections:
            return

        pc = RTCPeerConnection(RTC_CONFIGURATION)
        self.peer_connections[peer_id] = pc

        # Add data channel for chat
        data_channel = pc.createDataChannel("chat")
        self.data_channels[peer_id] = data_channel

        @data_channel.on("open")
        def on_open():
            logger.info(f"Data channel opened with {peer_id}")

        @data_channel.on("message")
        def on_message(message):
            try:
                data = json.loads(message)
                if data.get("type") == "chat":
                    self.message_received.emit(data.get("sender"), data.get("message"))
            except Exception as e:
                logger.error(f"Error processing chat message: {e}")

        @pc.on("icecandidate")
        async def on_icecandidate(candidate):
            await self.websocket.send(json.dumps({
                'type': 'ice-candidate',
                'target_id': peer_id,
                'candidate': candidate.to_json()
            }))

        @pc.on("track")
        async def on_track(track):
            if track.kind == "video":
                while True:
                    try:
                        frame = await track.recv()
                        img = frame.to_ndarray(format="rgb24")
                        height, width = img.shape[:2]
                        bytes_per_line = 3 * width
                        q_img = QImage(img.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
                        self.video_received.emit(peer_id, q_img)
                        if self.is_recording and self.recorder:
                            await self.recorder.addTrack(track)
                    except Exception as e:
                        logger.error(f"Error processing video frame: {e}")
                        break

        # Add local tracks
        pc.addTrack(self.video_track)
        pc.addTrack(self.audio_track)

        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)

        await self.websocket.send(json.dumps({
            'type': 'offer',
            'target_id': peer_id,
            'offer': pc.localDescription.sdp
        }))

    async def handle_offer(self, data):
        peer_id = data['sender_id']
        if peer_id not in self.peer_connections:
            await self.create_peer_connection(peer_id)

        pc = self.peer_connections[peer_id]
        await pc.setRemoteDescription(RTCSessionDescription(
            sdp=data['offer'], type="offer"
        ))

        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        await self.websocket.send(json.dumps({
            'type': 'answer',
            'target_id': peer_id,
            'answer': pc.localDescription.sdp
        }))

    async def handle_answer(self, data):
        peer_id = data['sender_id']
        if peer_id in self.peer_connections:
            pc = self.peer_connections[peer_id]
            await pc.setRemoteDescription(RTCSessionDescription(
                sdp=data['answer'], type="answer"
            ))

    async def handle_ice_candidate(self, data):
        peer_id = data['sender_id']
        if peer_id in self.peer_connections:
            pc = self.peer_connections[peer_id]
            await pc.addIceCandidate(RTCIceCandidate(
                candidate=data['candidate']['candidate'],
                sdpMid=data['candidate']['sdpMid'],
                sdpMLineIndex=data['candidate']['sdpMLineIndex']
            ))

    def run(self):
        asyncio.run(self._run())

    async def _run(self):
        await self.connect()
        await self.handle_signaling()

    def stop(self):
        self.running = False
        if self.websocket:
            asyncio.run(self.websocket.close())
            self.websocket = None
            
        for pc in self.peer_connections.values():
            asyncio.run(pc.close())
        self.peer_connections.clear()
        
        if self.recorder and self.is_recording:
            asyncio.run(self.recorder.stop())
            self.is_recording = False
            self.recording_status.emit(False)

    def set_mic_muted(self, muted):
        self.audio_track.set_muted(muted)

    def set_camera_muted(self, muted):
        self.video_track.set_muted(muted)

    def send_message(self, message):
        """Send chat message to all peers"""
        data = {
            "type": "chat",
            "sender": self.display_name,
            "message": message
        }
        for peer_id, data_channel in self.data_channels.items():
            if data_channel.readyState == "open":
                data_channel.send(json.dumps(data))

class VideoFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #1E1E1E;
                border-radius: 8px;
                border: 1px solid #333333;
            }
        """)
        self.setMinimumSize(320, 180)
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setMinimumSize(320, 180)
        self.name_label = QLabel(self)
        self.name_label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: rgba(0, 0, 0, 0.5);
                padding: 4px;
                border-radius: 4px;
            }
        """)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.name_label.hide()

    def update_frame(self, image):
        self.label.setPixmap(QPixmap.fromImage(image).scaled(
            self.label.size(), Qt.AspectRatioMode.KeepAspectRatio
        ))

    def set_name(self, name):
        self.name_label.setText(name)
        self.name_label.show()

class TestDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Test Camera and Microphone")
        self.setFixedSize(800, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: #121212;
            }
            QLabel {
                color: #FFFFFF;
                font-size: 14px;
            }
            QPushButton {
                background-color: #2D2D2D;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #3D3D3D;
            }
            QPushButton:checked {
                background-color: #FF4444;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Camera test section
        camera_group = QFrame()
        camera_group.setStyleSheet("""
            QFrame {
                background-color: #1E1E1E;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        camera_layout = QVBoxLayout(camera_group)

        camera_label = QLabel("Camera Test")
        camera_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        camera_layout.addWidget(camera_label)

        self.camera_frame = VideoFrame()
        self.camera_frame.setMinimumSize(640, 480)
        camera_layout.addWidget(self.camera_frame)

        self.camera_button = QPushButton("Enable Camera")
        self.camera_button.setCheckable(True)
        self.camera_button.clicked.connect(self.toggle_camera)
        camera_layout.addWidget(self.camera_button)

        layout.addWidget(camera_group)

        # Microphone test section
        mic_group = QFrame()
        mic_group.setStyleSheet("""
            QFrame {
                background-color: #1E1E1E;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        mic_layout = QVBoxLayout(mic_group)

        mic_label = QLabel("Microphone Test")
        mic_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        mic_layout.addWidget(mic_label)

        self.mic_button = QPushButton("Enable Microphone")
        self.mic_button.setCheckable(True)
        self.mic_button.clicked.connect(self.toggle_microphone)
        mic_layout.addWidget(self.mic_button)

        # Volume meter
        self.volume_meter = QFrame()
        self.volume_meter.setStyleSheet("""
            QFrame {
                background-color: #2D2D2D;
                border-radius: 4px;
                min-height: 20px;
            }
        """)
        self.volume_meter.setMinimumHeight(20)
        mic_layout.addWidget(self.volume_meter)

        layout.addWidget(mic_group)

        # Buttons
        button_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Initialize test devices
        self.camera = None
        self.audio_stream = None
        self.volume_timer = QTimer()
        self.volume_timer.timeout.connect(self.update_volume_meter)
        self.volume_timer.setInterval(50)  # 20 FPS

    def toggle_camera(self):
        if self.camera_button.isChecked():
            self.start_camera()
        else:
            self.stop_camera()

    def start_camera(self):
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                raise Exception("Failed to open camera")
            
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            self.camera_timer = QTimer()
            self.camera_timer.timeout.connect(self.update_camera_frame)
            self.camera_timer.start(33)  # ~30 FPS
            
            self.camera_button.setText("Disable Camera")
        except Exception as e:
            logger.error(f"Failed to start camera: {e}")
            self.camera_button.setChecked(False)
            QMessageBox.critical(self, "Error", "Failed to start camera")

    def stop_camera(self):
        if self.camera:
            self.camera_timer.stop()
            self.camera.release()
            self.camera = None
            self.camera_frame.update_frame(QImage())
        self.camera_button.setText("Enable Camera")

    def update_camera_frame(self):
        if self.camera:
            ret, frame = self.camera.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                height, width = frame.shape[:2]
                bytes_per_line = 3 * width
                image = QImage(frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
                self.camera_frame.update_frame(image)

    def toggle_microphone(self):
        if self.mic_button.isChecked():
            self.start_microphone()
        else:
            self.stop_microphone()

    def start_microphone(self):
        try:
            import sounddevice as sd
            import numpy as np
            
            def audio_callback(indata, frames, time, status):
                if status:
                    logger.warning(f"Audio capture status: {status}")
                self.current_volume = np.abs(indata).mean()
            
            self.audio_stream = sd.InputStream(
                channels=1,
                samplerate=48000,
                callback=audio_callback,
                blocksize=1024,
                dtype=np.float32
            )
            
            self.audio_stream.start()
            self.volume_timer.start()
            self.mic_button.setText("Disable Microphone")
            self.current_volume = 0
        except Exception as e:
            logger.error(f"Failed to start microphone: {e}")
            self.mic_button.setChecked(False)
            QMessageBox.critical(self, "Error", "Failed to start microphone")

    def stop_microphone(self):
        if self.audio_stream:
            self.volume_timer.stop()
            self.audio_stream.stop()
            self.audio_stream.close()
            self.audio_stream = None
            self.update_volume_meter()
        self.mic_button.setText("Enable Microphone")

    def update_volume_meter(self):
        if hasattr(self, 'current_volume'):
            volume = min(1.0, self.current_volume * 10)  # Scale volume for better visibility
            self.volume_meter.setStyleSheet(f"""
                QFrame {{
                    background-color: qlineargradient(x1:0, y1:0, x2:{volume}, y2:0,
                        stop:0 #FF4444, stop:1 #4CAF50);
                    border-radius: 4px;
                    min-height: 20px;
                }}
            """)
        else:
            self.volume_meter.setStyleSheet("""
                QFrame {
                    background-color: #2D2D2D;
                    border-radius: 4px;
                    min-height: 20px;
                }
            """)

    def closeEvent(self, event):
        self.stop_camera()
        self.stop_microphone()
        event.accept()

    def get_device_status(self):
        return {
            'camera_enabled': self.camera_button.isChecked(),
            'microphone_enabled': self.mic_button.isChecked()
        }

def load_saved_user():
    try:
        if os.path.exists('user_data.json'):
            with open('user_data.json', 'r') as f:
                data = json.load(f)
                if data.get('remember_me'):
                    return data
    except Exception:
        pass
    return None

def main():
    app = QApplication(sys.argv)
    
    # Try to load saved user data
    saved_user = load_saved_user()
    
    if saved_user:
        # Create session to get fresh user object
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            user = session.query(User).filter_by(id=saved_user['user_id']).first()
            if user:
                # Update user's online status
                user.is_online = True
                session.commit()
                
                # Show main menu directly
                main_menu = MainMenu(user)
                main_menu.show()
                sys.exit(app.exec())
        finally:
            session.close()
    
    # Show login dialog if no saved user or login failed
    login_dialog = LoginDialog()
    if login_dialog.exec() == QDialog.DialogCode.Accepted:
        current_user = login_dialog.user
        if not current_user:
            QMessageBox.critical(None, "Error", "Login failed!")
            sys.exit(1)
            
        # Save user data if "Remember me" is checked
        if login_dialog.remember_me:
            user_data = {
                'user_id': current_user.id,
                'username': current_user.username,
                'remember_me': True
            }
            with open('user_data.json', 'w') as f:
                json.dump(user_data, f)
            
        # Show main menu
        main_menu = MainMenu(current_user)
        main_menu.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)

if __name__ == "__main__":
    main() 
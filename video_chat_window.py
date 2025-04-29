import sys
import json
import logging
import os
from datetime import datetime
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QPushButton, QFrame, QScrollArea, QLineEdit, QMessageBox,
                           QFileDialog, QMenu, QSystemTrayIcon, QDialog, QFormLayout, QCheckBox, QTextEdit)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QFont, QImage, QPixmap, QAction
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from init_db import User
from webrtc_client import WebRTCClient
from video_frame import VideoFrame

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Chat")
        self.setMinimumSize(1200, 800)
        
        # Set dark theme with improved colors and modern design
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212;
            }
            QLabel {
                color: #FFFFFF;
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
            QPushButton:pressed {
                background-color: #4D4D4D;
            }
            QPushButton:disabled {
                background-color: #1D1D1D;
                color: #666666;
            }
            QLineEdit {
                background-color: #2D2D2D;
                color: #FFFFFF;
                border: 1px solid #3D3D3D;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #4D4D4D;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #1E1E1E;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #3D3D3D;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        # Create system tray icon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("icons/videocam.svg"))
        
        # Create tray menu
        tray_menu = QMenu()
        show_action = QAction("Show", self)
        quit_action = QAction("Quit", self)
        show_action.triggered.connect(self.show)
        quit_action.triggered.connect(self.close)
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Left panel (video grid)
        left_panel = QWidget()
        left_panel.setMinimumWidth(800)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(20)

        # Video grid
        self.video_grid = QWidget()
        self.video_grid_layout = QVBoxLayout(self.video_grid)
        self.video_grid_layout.setContentsMargins(0, 0, 0, 0)
        self.video_grid_layout.setSpacing(20)

        # Add local video frame
        self.local_video = VideoFrame()
        self.video_grid_layout.addWidget(self.local_video)

        # Add video grid to scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.video_grid)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #1E1E1E;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #3D3D3D;
                min-height: 20px;
                border-radius: 4px;
            }
        """)

        left_layout.addWidget(scroll_area)

        # Right panel (chat)
        right_panel = QWidget()
        right_panel.setMinimumWidth(300)
        right_panel.setMaximumWidth(400)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(20)

        # Chat header
        chat_header = QLabel("Chat")
        chat_header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        chat_header.setStyleSheet("padding: 10px;")
        right_layout.addWidget(chat_header)

        # Chat messages area
        self.chat_messages = QWidget()
        self.chat_messages.setStyleSheet("""
            QWidget {
                background-color: #1E1E1E;
                border-radius: 8px;
            }
        """)
        self.chat_messages_layout = QVBoxLayout(self.chat_messages)
        self.chat_messages_layout.setContentsMargins(10, 10, 10, 10)
        self.chat_messages_layout.setSpacing(5)

        chat_scroll = QScrollArea()
        chat_scroll.setWidget(self.chat_messages)
        chat_scroll.setWidgetResizable(True)
        chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        chat_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #1E1E1E;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #3D3D3D;
                min-height: 20px;
                border-radius: 4px;
            }
        """)
        right_layout.addWidget(chat_scroll)

        # Chat input area
        chat_input = QWidget()
        chat_input_layout = QHBoxLayout(chat_input)
        chat_input_layout.setContentsMargins(0, 0, 0, 0)
        chat_input_layout.setSpacing(10)

        # Message input
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type a message...")
        self.message_input.returnPressed.connect(self.send_message)
        chat_input_layout.addWidget(self.message_input)

        # Send button
        send_button = QPushButton("Send")
        send_button.setFixedWidth(80)
        send_button.clicked.connect(self.send_message)
        chat_input_layout.addWidget(send_button)

        right_layout.addWidget(chat_input)

        # Add panels to main layout
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)

        # Control buttons at the bottom
        control_buttons = QWidget()
        control_buttons_layout = QHBoxLayout(control_buttons)
        control_buttons_layout.setContentsMargins(0, 0, 0, 0)
        control_buttons_layout.setSpacing(20)

        # Add control buttons with improved styling
        self.mic_button = QPushButton("Mic")
        self.mic_button.setIcon(QIcon("icons/mic.svg"))
        self.mic_button.setIconSize(QSize(24, 24))
        self.mic_button.setFixedHeight(40)
        self.mic_button.setCheckable(True)
        self.mic_button.setStyleSheet("""
            QPushButton {
                background-color: #2D2D2D;
                border-radius: 20px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #3D3D3D;
            }
            QPushButton:checked {
                background-color: #4CAF50;
            }
        """)
        self.mic_button.clicked.connect(self.toggle_mic)
        control_buttons_layout.addWidget(self.mic_button)

        self.camera_button = QPushButton("Camera")
        self.camera_button.setIcon(QIcon("icons/videocam.svg"))
        self.camera_button.setIconSize(QSize(24, 24))
        self.camera_button.setFixedHeight(40)
        self.camera_button.setCheckable(True)
        self.camera_button.setStyleSheet("""
            QPushButton {
                background-color: #2D2D2D;
                border-radius: 20px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #3D3D3D;
            }
            QPushButton:checked {
                background-color: #4CAF50;
            }
        """)
        self.camera_button.clicked.connect(self.toggle_camera)
        control_buttons_layout.addWidget(self.camera_button)

        self.record_button = QPushButton("Record")
        self.record_button.setIcon(QIcon("icons/record.svg"))
        self.record_button.setIconSize(QSize(24, 24))
        self.record_button.setFixedHeight(40)
        self.record_button.setCheckable(True)
        self.record_button.setStyleSheet("""
            QPushButton {
                background-color: #2D2D2D;
                border-radius: 20px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #3D3D3D;
            }
            QPushButton:checked {
                background-color: #FF4444;
            }
        """)
        self.record_button.clicked.connect(self.toggle_recording)
        control_buttons_layout.addWidget(self.record_button)

        # Add load history button
        self.load_history_button = QPushButton("Load History")
        self.load_history_button.clicked.connect(self.load_message_history)
        control_buttons_layout.addWidget(self.load_history_button)
        
        # Add clear history button
        self.clear_history_button = QPushButton("Clear History")
        self.clear_history_button.clicked.connect(self.clear_message_history)
        control_buttons_layout.addWidget(self.clear_history_button)

        end_call_button = QPushButton("End Call")
        end_call_button.setIcon(QIcon("icons/call_end.svg"))
        end_call_button.setIconSize(QSize(24, 24))
        end_call_button.setFixedHeight(40)
        end_call_button.setStyleSheet("""
            QPushButton {
                background-color: #FF4444;
                border-radius: 20px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #FF5555;
            }
        """)
        end_call_button.clicked.connect(self.end_call)
        control_buttons_layout.addWidget(end_call_button)

        left_layout.addWidget(control_buttons)

        # Add connection status indicator with improved styling
        self.connection_status = QLabel("Connected")
        self.connection_status.setStyleSheet("""
            QLabel {
                color: #4CAF50;
                padding: 8px;
                background-color: rgba(76, 175, 80, 0.1);
                border-radius: 8px;
            }
        """)
        status_layout = QHBoxLayout()
        status_layout.addWidget(self.connection_status)
        left_layout.addLayout(status_layout)

        # Initialize WebRTC client
        self.webrtc_client = None
        self.video_frames = {}
        self.is_recording = False

    def start_call(self, room_id, display_name, server_url):
        if self.webrtc_client:
            self.webrtc_client.stop()
            self.webrtc_client.wait()
        
        self.webrtc_client = WebRTCClient(room_id, display_name, server_url)
        self.webrtc_client.video_received.connect(self.handle_video_received)
        self.webrtc_client.user_joined.connect(self.handle_user_joined)
        self.webrtc_client.user_left.connect(self.handle_user_left)
        self.webrtc_client.message_received.connect(self.handle_message_received)
        self.webrtc_client.start()

        # Set initial device states
        self.webrtc_client.set_mic_muted(False)
        self.webrtc_client.set_camera_muted(False)

    def handle_video_received(self, peer_id, image):
        if peer_id not in self.video_frames:
            video_frame = VideoFrame()
            self.video_grid_layout.addWidget(video_frame)
            self.video_frames[peer_id] = video_frame
        self.video_frames[peer_id].update_frame(image)

    def handle_user_joined(self, peer_id, name):
        if peer_id in self.video_frames:
            self.video_frames[peer_id].set_name(name)

    def handle_user_left(self, peer_id):
        if peer_id in self.video_frames:
            self.video_frames[peer_id].deleteLater()
            del self.video_frames[peer_id]

    def handle_message_received(self, sender, message):
        """Handle incoming chat message"""
        message_widget = QWidget()
        message_layout = QVBoxLayout(message_widget)
        message_layout.setContentsMargins(0, 0, 0, 0)
        message_layout.setSpacing(5)

        sender_label = QLabel(sender)
        sender_label.setStyleSheet("""
            QLabel {
                color: #4CAF50;
                font-weight: bold;
            }
        """)

        message_label = QLabel(message)
        message_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                padding: 5px;
                background-color: #2D2D2D;
                border-radius: 8px;
            }
        """)
        message_label.setWordWrap(True)

        message_layout.addWidget(sender_label)
        message_layout.addWidget(message_label)
        self.chat_messages_layout.addWidget(message_widget)

        # Scroll to bottom
        scroll_area = self.chat_messages.parent().parent()
        if scroll_area:
            scroll_area.verticalScrollBar().setValue(
                scroll_area.verticalScrollBar().maximum()
            )

    def send_message(self):
        """Send chat message"""
        message = self.message_input.text().strip()
        if message and self.webrtc_client:
            self.webrtc_client.send_message(message)
            self.message_input.clear()
            self.handle_message_received(self.webrtc_client.display_name, message)

    def toggle_recording(self):
        if not self.is_recording:
            file_name, _ = QFileDialog.getSaveFileName(
                self,
                "Save Recording",
                f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                "MP4 Files (*.mp4)"
            )
            if file_name:
                self.webrtc_client.start_recording(file_name)
                self.record_button.setIcon(QIcon("icons/stop.svg"))
                self.record_button.setText("Stop Recording")
                self.record_button.setChecked(True)
                self.is_recording = True
        else:
            self.webrtc_client.stop_recording()
            self.record_button.setIcon(QIcon("icons/record.svg"))
            self.record_button.setText("Record")
            self.record_button.setChecked(False)
            self.is_recording = False

    def toggle_mic(self):
        is_muted = not self.mic_button.isChecked()
        self.webrtc_client.set_mic_muted(is_muted)
        self.mic_button.setIcon(QIcon("icons/mic_off.svg" if is_muted else "icons/mic.svg"))

    def toggle_camera(self):
        is_muted = not self.camera_button.isChecked()
        self.webrtc_client.set_camera_muted(is_muted)
        self.camera_button.setIcon(QIcon("icons/videocam_off.svg" if is_muted else "icons/videocam.svg"))

    def end_call(self):
        if self.webrtc_client:
            self.webrtc_client.stop()
            self.webrtc_client = None
        self.close()

    def closeEvent(self, event):
        if self.webrtc_client:
            self.webrtc_client.stop()
            self.webrtc_client.wait()  # Wait for thread to finish
            self.webrtc_client = None
        
        if hasattr(self, 'current_user'):
            # Update user status to offline
            engine = create_engine('sqlite:///chat.db')
            Session = sessionmaker(bind=engine)
            session = Session()
            try:
                user = session.query(User).filter_by(id=self.current_user.id).first()
                if user:
                    user.is_online = False
                    session.commit()
            finally:
                session.close()
            
        event.accept()

    def load_message_history(self):
        try:
            response = requests.get(f'http://localhost:5000/messages/{self.current_user.room_id}')
            if response.status_code == 200:
                messages = response.json()
                for msg in messages:
                    self.handle_message_received(msg['user'], msg['content'])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load message history: {str(e)}")

    def clear_message_history(self):
        try:
            response = requests.delete(f'http://localhost:5000/messages/{self.current_user.room_id}')
            if response.status_code == 200:
                # Clear all messages from the chat layout
                while self.chat_messages_layout.count():
                    item = self.chat_messages_layout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()
                QMessageBox.information(self, "Success", "Message history cleared")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to clear message history: {str(e)}")

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
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Video/avatar label
        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(320, 180)
        layout.addWidget(self.video_label)
        
        # Name label
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
        layout.addWidget(self.name_label)
        
        # Camera off overlay
        self.camera_off_overlay = QLabel(self)
        self.camera_off_overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_off_overlay.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 0.7);
                border-radius: 8px;
            }
        """)
        self.camera_off_overlay.hide()
        layout.addWidget(self.camera_off_overlay)
        
    def update_frame(self, image, user=None):
        if image is None and user and user.avatar_path and os.path.exists(user.avatar_path):
            # Show avatar when camera is off
            pixmap = QPixmap(user.avatar_path)
            self.video_label.setPixmap(pixmap.scaled(
                self.video_label.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            ))
            self.camera_off_overlay.show()
        else:
            # Show video frame
            self.video_label.setPixmap(QPixmap.fromImage(image).scaled(
                self.video_label.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            ))
            self.camera_off_overlay.hide()
            
    def set_name(self, name):
        self.name_label.setText(name)
        self.name_label.show() 
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QListWidget, QFrame, QDialog, QLineEdit, QMessageBox)
from PyQt6.QtCore import Qt
from test_dialog import TestDialog
from create_room_dialog import CreateRoomDialog
from settings_dialog import SettingsDialog
from video_chat_window import MainWindow
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from init_db import User, Room
from config import DATABASE_URL

class MainMenu(QMainWindow):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.setWindowTitle("Video Chat - Main Menu")
        self.setMinimumSize(800, 600)
        
        # Set window properties
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212;
            }
        """)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Left panel (rooms list)
        left_panel = QFrame()
        left_panel.setStyleSheet("""
            QFrame {
                background-color: #1E1E1E;
                border-radius: 10px;
                border: 1px solid #333333;
            }
        """)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(20, 20, 20, 20)
        left_layout.setSpacing(15)
        
        # User info
        user_info = QLabel(f"Logged in as: {self.current_user.get_display_name()}")
        user_info.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
            }
        """)
        left_layout.addWidget(user_info)
        
        # Settings button
        settings_button = QPushButton("Settings")
        settings_button.setStyleSheet("""
            QPushButton {
                background-color: #6C63FF;
                border: none;
                border-radius: 5px;
                padding: 10px;
                color: white;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #5952D9;
            }
        """)
        settings_button.clicked.connect(self.show_settings)
        left_layout.addWidget(settings_button)
        
        # Rooms header
        rooms_header = QLabel("Your Rooms")
        rooms_header.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 20px;
                font-weight: bold;
            }
        """)
        left_layout.addWidget(rooms_header)
        
        # Rooms list
        self.rooms_list = QListWidget()
        self.rooms_list.setStyleSheet("""
            QListWidget {
                background-color: #2D2D2D;
                border: 1px solid #3D3D3D;
                border-radius: 5px;
                color: white;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #3D3D3D;
            }
            QListWidget::item:selected {
                background-color: #6C63FF;
            }
        """)
        self.rooms_list.itemDoubleClicked.connect(self.join_room)
        left_layout.addWidget(self.rooms_list)
        
        # Create room button
        create_room_button = QPushButton("Create Room")
        create_room_button.setStyleSheet("""
            QPushButton {
                background-color: #6C63FF;
                border: none;
                border-radius: 5px;
                padding: 10px;
                color: white;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #5952D9;
            }
        """)
        create_room_button.clicked.connect(self.create_room)
        left_layout.addWidget(create_room_button)
        
        # Test devices button
        test_devices_button = QPushButton("Test Devices")
        test_devices_button.setStyleSheet("""
            QPushButton {
                background-color: #2D2D2D;
                border: 1px solid #6C63FF;
                border-radius: 5px;
                padding: 10px;
                color: #6C63FF;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3D3D3D;
            }
        """)
        test_devices_button.clicked.connect(self.test_devices)
        left_layout.addWidget(test_devices_button)
        
        main_layout.addWidget(left_panel)
        
        # Load rooms
        self.load_rooms()
        
    def load_rooms(self):
        # Create a new session
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Merge the detached user instance with the new session
            self.current_user = session.merge(self.current_user)
            
            # Now we can safely query the user and their rooms
            user = session.query(User).filter_by(id=self.current_user.id).first()
            if user:
                self.rooms_list.clear()
                for room in user.rooms:
                    item_text = f"{room.name}"
                    self.rooms_list.addItem(item_text)
        finally:
            session.close()
            
    def create_room(self):
        dialog = CreateRoomDialog(self.current_user, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_rooms()
            
    def join_room(self, item):
        room_name = item.text()
        
        # Create a new session
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Get room
            room = session.query(Room).filter_by(name=room_name).first()
            if room:
                # Create video chat window
                self.video_chat = MainWindow(self.current_user, room)
                self.video_chat.show()
                self.hide()
        finally:
            session.close()
            
    def test_devices(self):
        dialog = TestDialog(self)
        dialog.exec()
        
    def show_settings(self):
        settings_dialog = SettingsDialog(self.current_user, self)
        if settings_dialog.exec() == QDialog.DialogCode.Accepted:
            # Create a new session
            engine = create_engine(DATABASE_URL)
            Session = sessionmaker(bind=engine)
            session = Session()
            
            try:
                # Merge the current user with the new session
                self.current_user = session.merge(self.current_user)
                
                # Update the user object
                self.current_user.nickname = settings_dialog.nickname_input.text()
                if settings_dialog.new_avatar_path:
                    self.current_user.avatar_path = settings_dialog.new_avatar_path
                
                session.commit()
                self.update_user_info()
                self.load_rooms()
            finally:
                session.close()
        elif settings_dialog.result() == QDialog.DialogCode.Rejected:
            # User switched accounts
            self.close() 
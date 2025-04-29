from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QWidget, QHBoxLayout, QCheckBox
from PyQt6.QtCore import Qt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from init_db import Room, User
from config import (DATABASE_URL, THEME)

class CreateRoomDialog(QDialog):
    def __init__(self, current_user, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.room = None
        self.setWindowTitle("Create Room")
        self.setMinimumWidth(300)
        
        # Set window properties
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.init_ui()
        
    def init_ui(self):
        # Main layout with padding
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Create a form container with background
        form_container = QWidget(self)
        form_container.setObjectName("formContainer")
        form_container.setStyleSheet(f"""
            #formContainer {{
                background-color: {THEME['panel_background']};
                border-radius: 10px;
                border: 1px solid {THEME['border_color']};
            }}
        """)
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(15)
        
        # Title
        title = QLabel("Create New Room")
        title.setStyleSheet(f"""
            QLabel {{
                color: {THEME['text_color']};
                font-size: 20px;
                font-weight: bold;
            }}
        """)
        form_layout.addWidget(title)
        
        # Room name input
        name_layout = QHBoxLayout()
        name_label = QLabel("Room Name:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Room Name")
        self.name_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {THEME['button_background']};
                border: 1px solid {THEME['border_color']};
                border-radius: 5px;
                padding: 10px;
                color: {THEME['text_color']};
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 1px solid {THEME['accent_color']};
            }}
        """)
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        form_layout.addLayout(name_layout)
        
        # Public room checkbox
        self.public_checkbox = QCheckBox("Make room public")
        form_layout.addWidget(self.public_checkbox)
        
        # Create button
        create_button = QPushButton("Create Room")
        create_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['accent_color']};
                border: none;
                border-radius: 5px;
                padding: 10px;
                color: {THEME['text_color']};
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {THEME['button_hover']};
            }}
            QPushButton:pressed {{
                background-color: {THEME['button_pressed']};
            }}
        """)
        create_button.clicked.connect(self.create_room)
        form_layout.addWidget(create_button)
        
        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 2px solid {THEME['accent_color']};
                border-radius: 5px;
                padding: 10px;
                color: {THEME['accent_color']};
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: rgba(108, 99, 255, 0.1);
            }}
            QPushButton:pressed {{
                background-color: rgba(108, 99, 255, 0.2);
            }}
        """)
        cancel_button.clicked.connect(self.reject)
        form_layout.addWidget(cancel_button)
        
        layout.addWidget(form_container)
        self.setLayout(layout)
        
    def create_room(self):
        room_name = self.name_input.text().strip()
        is_public = self.public_checkbox.isChecked()
        
        if not room_name:
            QMessageBox.warning(self, "Error", "Please enter a room name")
            return
            
        # Create a new session
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Check if room name already exists
            existing_room = session.query(Room).filter_by(name=room_name).first()
            if existing_room:
                QMessageBox.warning(self, "Error", "A room with this name already exists")
                return
                
            # Get fresh user object from new session
            user = session.query(User).filter_by(id=self.current_user.id).first()
            if not user:
                QMessageBox.critical(self, "Error", "User not found")
                return
                
            # Create new room
            room = Room(
                name=room_name,
                is_public=is_public,
                created_by=user
            )
            room.users.append(user)
            session.add(room)
            session.commit()
            
            QMessageBox.information(self, "Success", "Room created successfully")
            self.accept()
            
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Error", f"Failed to create room: {str(e)}")
        finally:
            session.close() 
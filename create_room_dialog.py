from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QWidget
from PyQt6.QtCore import Qt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from init_db import Room, User

class CreateRoomDialog(QDialog):
    def __init__(self, current_user, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.room = None
        self.setWindowTitle("Create New Room")
        self.setFixedWidth(300)
        
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
        form_container.setStyleSheet("""
            #formContainer {
                background-color: #1E1E1E;
                border-radius: 10px;
                border: 1px solid #333333;
            }
        """)
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(15)
        
        # Title
        title = QLabel("Create New Room")
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 20px;
                font-weight: bold;
            }
        """)
        form_layout.addWidget(title)
        
        # Room name input
        self.room_name_input = QLineEdit()
        self.room_name_input.setPlaceholderText("Room Name")
        self.room_name_input.setStyleSheet("""
            QLineEdit {
                background-color: #2D2D2D;
                border: 1px solid #3D3D3D;
                border-radius: 5px;
                padding: 10px;
                color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #6C63FF;
            }
        """)
        form_layout.addWidget(self.room_name_input)
        
        # Create button
        create_button = QPushButton("Create Room")
        create_button.setStyleSheet("""
            QPushButton {
                background-color: #6C63FF;
                border: none;
                border-radius: 5px;
                padding: 10px;
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5952D9;
            }
            QPushButton:pressed {
                background-color: #4842B3;
            }
        """)
        create_button.clicked.connect(self.create_room)
        form_layout.addWidget(create_button)
        
        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 2px solid #6C63FF;
                border-radius: 5px;
                padding: 10px;
                color: #6C63FF;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(108, 99, 255, 0.1);
            }
            QPushButton:pressed {
                background-color: rgba(108, 99, 255, 0.2);
            }
        """)
        cancel_button.clicked.connect(self.reject)
        form_layout.addWidget(cancel_button)
        
        layout.addWidget(form_container)
        self.setLayout(layout)
        
    def create_room(self):
        room_name = self.room_name_input.text().strip()
        if not room_name:
            QMessageBox.warning(self, "Error", "Please enter a room name")
            return
            
        # Create a new session
        engine = create_engine('sqlite:///chat.db')
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Get fresh user object from new session
            user = session.query(User).filter_by(id=self.current_user.id).first()
            if not user:
                QMessageBox.critical(self, "Error", "User not found")
                return
                
            # Create new room
            room = Room(name=room_name)
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
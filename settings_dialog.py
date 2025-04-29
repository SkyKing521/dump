from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QPushButton, QMessageBox, QFileDialog,
                           QFrame, QWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QImage
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from init_db import User
from config import DATABASE_URL
import os
import shutil

class SettingsDialog(QDialog):
    def __init__(self, current_user, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.setWindowTitle("Settings")
        self.setFixedWidth(400)
        self.init_ui()
        
    def init_ui(self):
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
        title = QLabel("Profile Settings")
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 20px;
                font-weight: bold;
            }
        """)
        form_layout.addWidget(title)
        
        # Avatar section
        avatar_layout = QHBoxLayout()
        
        # Avatar preview
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(100, 100)
        self.avatar_label.setStyleSheet("""
            QLabel {
                background-color: #2D2D2D;
                border-radius: 50px;
                border: 2px solid #6C63FF;
            }
        """)
        self.update_avatar_preview()
        avatar_layout.addWidget(self.avatar_label)
        
        # Avatar buttons
        avatar_buttons_layout = QVBoxLayout()
        
        change_avatar_button = QPushButton("Change Avatar")
        change_avatar_button.setStyleSheet("""
            QPushButton {
                background-color: #6C63FF;
                border: none;
                border-radius: 5px;
                padding: 8px;
                color: white;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #5952D9;
            }
        """)
        change_avatar_button.clicked.connect(self.change_avatar)
        avatar_buttons_layout.addWidget(change_avatar_button)
        
        remove_avatar_button = QPushButton("Remove Avatar")
        remove_avatar_button.setStyleSheet("""
            QPushButton {
                background-color: #FF4444;
                border: none;
                border-radius: 5px;
                padding: 8px;
                color: white;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #CC0000;
            }
        """)
        remove_avatar_button.clicked.connect(self.remove_avatar)
        avatar_buttons_layout.addWidget(remove_avatar_button)
        
        avatar_layout.addLayout(avatar_buttons_layout)
        form_layout.addLayout(avatar_layout)
        
        # Nickname
        nickname_label = QLabel("Nickname")
        nickname_label.setStyleSheet("color: white;")
        form_layout.addWidget(nickname_label)
        
        self.nickname_input = QLineEdit()
        self.nickname_input.setPlaceholderText("Enter your nickname")
        self.nickname_input.setText(self.current_user.nickname or "")
        self.nickname_input.setStyleSheet("""
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
        form_layout.addWidget(self.nickname_input)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        save_button = QPushButton("Save")
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #6C63FF;
                border: none;
                border-radius: 5px;
                padding: 10px;
                color: white;
                font-size: 14px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #5952D9;
            }
        """)
        save_button.clicked.connect(self.save_settings)
        buttons_layout.addWidget(save_button)
        
        switch_account_button = QPushButton("Switch Account")
        switch_account_button.setStyleSheet("""
            QPushButton {
                background-color: #FF4444;
                border: none;
                border-radius: 5px;
                padding: 10px;
                color: white;
                font-size: 14px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #CC0000;
            }
        """)
        switch_account_button.clicked.connect(self.switch_account)
        buttons_layout.addWidget(switch_account_button)
        
        form_layout.addLayout(buttons_layout)
        
        layout.addWidget(form_container)
        self.setLayout(layout)
        
    def update_avatar_preview(self):
        if self.current_user.avatar_path and os.path.exists(self.current_user.avatar_path):
            pixmap = QPixmap(self.current_user.avatar_path)
            self.avatar_label.setPixmap(pixmap.scaled(
                100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            ))
        else:
            # Set default avatar
            self.avatar_label.setPixmap(QPixmap())
            
    def change_avatar(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Avatar",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_path:
            # Create avatars directory if it doesn't exist
            avatars_dir = "avatars"
            if not os.path.exists(avatars_dir):
                os.makedirs(avatars_dir)
                
            # Copy file to avatars directory
            new_path = os.path.join(avatars_dir, f"{self.current_user.id}_{os.path.basename(file_path)}")
            shutil.copy2(file_path, new_path)
            
            # Update user's avatar path
            self.current_user.avatar_path = new_path
            
            # Update preview
            self.update_avatar_preview()
            
    def remove_avatar(self):
        if self.current_user.avatar_path and os.path.exists(self.current_user.avatar_path):
            try:
                os.remove(self.current_user.avatar_path)
            except Exception:
                pass
        self.current_user.avatar_path = None
        self.update_avatar_preview()
        
    def save_settings(self):
        # Create a new session
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Get fresh user object
            user = session.query(User).filter_by(id=self.current_user.id).first()
            if not user:
                QMessageBox.critical(self, "Error", "User not found")
                return
                
            # Update user's nickname
            user.nickname = self.nickname_input.text().strip() or None
            user.avatar_path = self.current_user.avatar_path
            
            session.commit()
            self.current_user = user
            QMessageBox.information(self, "Success", "Settings saved successfully")
            self.accept()
            
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")
        finally:
            session.close()
            
    def switch_account(self):
        # Clear saved user data
        try:
            if os.path.exists('user_data.json'):
                os.remove('user_data.json')
        except Exception:
            pass
            
        self.reject() 
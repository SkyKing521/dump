from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QPushButton, QMessageBox, QCheckBox, QWidget)
from PyQt6.QtCore import QSettings, Qt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import check_password_hash
from init_db import User
from config import DATABASE_URL
import os

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login")
        self.setFixedWidth(300)
        self.user = None
        self.remember_me = False
        
        # Set window properties
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Create database session
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        self.session = Session()
        
        # Load saved credentials if they exist
        self.settings = QSettings("WebRTCVideoChat", "Credentials")
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
        title = QLabel("Welcome Back")
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 20px;
                font-weight: bold;
            }
        """)
        form_layout.addWidget(title)
        
        # Username
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setStyleSheet("""
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
        # Load saved username
        saved_username = self.settings.value("username", "")
        if saved_username:
            self.username_input.setText(saved_username)
        form_layout.addWidget(self.username_input)
        
        # Password
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet(self.username_input.styleSheet())
        form_layout.addWidget(self.password_input)
        
        # Remember me checkbox
        self.remember_checkbox = QCheckBox("Remember me")
        self.remember_checkbox.setStyleSheet("""
            QCheckBox {
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 2px solid #6C63FF;
            }
            QCheckBox::indicator:unchecked {
                background-color: transparent;
            }
            QCheckBox::indicator:checked {
                background-color: #6C63FF;
                image: url(icons/checkmark.png);
            }
        """)
        self.remember_checkbox.setChecked(self.settings.value("remember_me", False, type=bool))
        form_layout.addWidget(self.remember_checkbox)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        login_button = QPushButton("Login")
        login_button.setStyleSheet("""
            QPushButton {
                background-color: #6C63FF;
                border: none;
                border-radius: 5px;
                padding: 10px;
                color: white;
                font-size: 14px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #5952D9;
            }
            QPushButton:pressed {
                background-color: #4842B3;
            }
        """)
        login_button.clicked.connect(self.login)
        button_layout.addWidget(login_button)
        
        # Register button
        register_button = QPushButton("Register")
        register_button.clicked.connect(self.handle_register)
        button_layout.addWidget(register_button)
        
        form_layout.addLayout(button_layout)
        
        layout.addWidget(form_container)
        self.setLayout(layout)
        
    def login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter both username and password")
            return
            
        try:
            user = self.session.query(User).filter_by(username=username).first()
            if user and check_password_hash(user.password_hash, password):
                self.user = user
                self.remember_me = self.remember_checkbox.isChecked()
                
                # Save credentials if remember me is checked
                if self.remember_me:
                    self.settings.setValue("username", username)
                    self.settings.setValue("remember_me", True)
                else:
                    self.settings.remove("username")
                    self.settings.remove("remember_me")
                
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "Invalid username or password")
        finally:
            self.session.close()
            
    def handle_register(self):
        from register_dialog import RegisterDialog
        register_dialog = RegisterDialog(self)
        if register_dialog.exec() == QDialog.DialogCode.Accepted:
            self.username_input.setText(register_dialog.username_input.text())
            self.password_input.setText(register_dialog.password_input.text())
        
    def closeEvent(self, event):
        self.session.close()
        event.accept() 
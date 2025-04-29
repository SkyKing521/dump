from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt6.QtCore import Qt
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from init_db import User
from config import DATABASE_URL
from werkzeug.security import generate_password_hash

class RegisterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Register")
        self.setFixedSize(300, 250)
        
        # Create layout
        layout = QVBoxLayout()
        
        # Username input
        self.username_label = QLabel("Username:")
        self.username_input = QLineEdit()
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)
        
        # Email input
        self.email_label = QLabel("Email:")
        self.email_input = QLineEdit()
        layout.addWidget(self.email_label)
        layout.addWidget(self.email_input)
        
        # Password input
        self.password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        
        # Confirm password input
        self.confirm_password_label = QLabel("Confirm Password:")
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.confirm_password_label)
        layout.addWidget(self.confirm_password_input)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        # Register button
        self.register_button = QPushButton("Register")
        self.register_button.clicked.connect(self.handle_register)
        buttons_layout.addWidget(self.register_button)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)
        
        # Center the dialog
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.center_on_screen()
        
    def center_on_screen(self):
        screen_geometry = self.screen().geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)
        
    def handle_register(self):
        username = self.username_input.text()
        email = self.email_input.text()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        
        # Validate inputs
        if not username or not email or not password or not confirm_password:
            QMessageBox.warning(self, "Error", "Please fill in all fields")
            return
            
        if password != confirm_password:
            QMessageBox.warning(self, "Error", "Passwords do not match")
            return
            
        # Create database session
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Check if username already exists
            existing_user = session.query(User).filter_by(username=username).first()
            if existing_user:
                QMessageBox.warning(self, "Error", "Username already exists")
                return
                
            # Check if email already exists
            existing_email = session.query(User).filter_by(email=email).first()
            if existing_email:
                QMessageBox.warning(self, "Error", "Email already registered")
                return
                
            # Create new user
            new_user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password)
            )
            session.add(new_user)
            session.commit()
            
            QMessageBox.information(self, "Success", "Registration successful!")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Registration failed: {str(e)}")
            
        finally:
            session.close() 
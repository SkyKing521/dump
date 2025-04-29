from PyQt6.QtWidgets import QFrame, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap

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
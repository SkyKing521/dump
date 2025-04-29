from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QFrame, QWidget)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap
import cv2
import sounddevice as sd
import numpy as np

class TestDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Test Devices")
        self.setFixedSize(800, 600)
        self.setup_ui()
        self.setup_devices()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Camera test
        self.camera_frame = QLabel()
        self.camera_frame.setFixedSize(640, 480)
        self.camera_frame.setStyleSheet("background-color: #1E1E1E; border-radius: 10px;")
        layout.addWidget(self.camera_frame)
        
        # Controls
        controls = QHBoxLayout()
        
        self.camera_btn = QPushButton("Test Camera")
        self.camera_btn.setCheckable(True)
        self.camera_btn.clicked.connect(self.toggle_camera)
        controls.addWidget(self.camera_btn)
        
        self.mic_btn = QPushButton("Test Microphone")
        self.mic_btn.setCheckable(True)
        self.mic_btn.clicked.connect(self.toggle_microphone)
        controls.addWidget(self.mic_btn)
        
        # Volume meter
        self.volume_meter = QFrame()
        self.volume_meter.setFixedHeight(20)
        self.volume_meter.setStyleSheet("background-color: #1E1E1E; border-radius: 5px;")
        controls.addWidget(self.volume_meter)
        
        layout.addLayout(controls)
        
    def setup_devices(self):
        self.camera = None
        self.camera_timer = QTimer()
        self.camera_timer.timeout.connect(self.update_camera)
        
        self.audio_stream = None
        self.volume_timer = QTimer()
        self.volume_timer.timeout.connect(self.update_volume)
        self.current_volume = 0
        
    def toggle_camera(self):
        if self.camera_btn.isChecked():
            self.camera = cv2.VideoCapture(0)
            if self.camera.isOpened():
                self.camera_timer.start(33)  # ~30 FPS
            else:
                self.camera_btn.setChecked(False)
        else:
            if self.camera:
                self.camera_timer.stop()
                self.camera.release()
                self.camera = None
                self.camera_frame.clear()
                
    def update_camera(self):
        if self.camera:
            ret, frame = self.camera.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame.shape
                img = QImage(frame.data, w, h, ch * w, QImage.Format.Format_RGB888)
                self.camera_frame.setPixmap(QPixmap.fromImage(img))
                
    def toggle_microphone(self):
        if self.mic_btn.isChecked():
            try:
                def audio_callback(indata, frames, time, status):
                    self.current_volume = np.abs(indata).mean()
                
                self.audio_stream = sd.InputStream(
                    channels=1,
                    samplerate=44100,
                    callback=audio_callback
                )
                self.audio_stream.start()
                self.volume_timer.start(50)
            except Exception as e:
                print(f"Error starting microphone: {e}")
                self.mic_btn.setChecked(False)
        else:
            if self.audio_stream:
                self.volume_timer.stop()
                self.audio_stream.stop()
                self.audio_stream.close()
                self.audio_stream = None
                self.volume_meter.setStyleSheet("background-color: #1E1E1E; border-radius: 5px;")
                
    def update_volume(self):
        if hasattr(self, 'current_volume'):
            volume = min(1.0, self.current_volume * 5)
            self.volume_meter.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:{volume}, y2:0,
                        stop:0 #4CAF50, stop:1 #1E1E1E);
                    border-radius: 5px;
                }}
            """)
            
    def closeEvent(self, event):
        if self.camera:
            self.camera_timer.stop()
            self.camera.release()
        if self.audio_stream:
            self.volume_timer.stop()
            self.audio_stream.stop()
            self.audio_stream.close()
        event.accept() 
# Server configuration
WEBSOCKET_SERVER = "ws://26.34.237.219:8765"
HTTP_SERVER = "http://26.34.237.219:5000"

# Database configuration
DATABASE_URL = "sqlite:///chat.db"

# Application settings
APP_NAME = "Video Chat"
APP_VERSION = "1.0.0"
MIN_WINDOW_WIDTH = 800
MIN_WINDOW_HEIGHT = 600

# UI settings
THEME = {
    "background_color": "#121212",
    "panel_background": "#1E1E1E",
    "button_background": "#2D2D2D",
    "button_hover": "#3D3D3D",
    "button_pressed": "#4D4D4D",
    "button_disabled": "#1D1D1D",
    "text_color": "#FFFFFF",
    "border_color": "#333333",
    "accent_color": "#6C63FF",
    "error_color": "#FF4444",
    "success_color": "#4CAF50"
}

# File paths
AVATARS_DIR = "avatars"
ICONS_DIR = "icons"
MESSAGE_STORAGE_DIR = "message_storage"

# Default user settings
DEFAULT_MIC_ENABLED = True
DEFAULT_CAMERA_ENABLED = True

# WebRTC configuration
ICE_SERVERS = [
    {"urls": "stun:stun.l.google.com:19302"},
    {"urls": "stun:stun1.l.google.com:19302"}
]

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s" 
import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLabel, QStackedWidget, QTextEdit,
    QFrame, QLineEdit, QPushButton, QScrollArea, QSizePolicy, 
    QFileDialog, QGridLayout, QDialog, QTabWidget, QFormLayout, QCheckBox,
    QInputDialog, QMessageBox
)
from PyQt5.QtGui import QPixmap, QIcon, QTextCursor, QFont, QImage, QPainter
from PyQt5.QtCore import Qt, QSize, QTimer, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import QTextBrowser

class EmojiPicker(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выберите смайлик")
        self.setFixedSize(300, 150)
        self.setStyleSheet("background-color: #2c2c3c;")
        
        layout = QGridLayout()
        emojis = ["😀", "😂", "😍", "🤔", "👍", "❤️", "🔥", "🎮", "📷", "🎧"]
        
        for i, emoji in enumerate(emojis):
            btn = QPushButton(emoji)
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 24px; 
                    border: none;
                    background: transparent;
                    padding: 10px;
                }
                QPushButton:hover {
                    background: #3a3a4a;
                    border-radius: 5px;
                }
            """)
            btn.clicked.connect(lambda _, e=emoji: self.emoji_selected(e))
            layout.addWidget(btn, i//5, i%5)
        
        self.setLayout(layout)
    
    def emoji_selected(self, emoji):
        self.parent().insert_emoji(emoji)
        self.close()

class ServerChannelWidget(QWidget):
    def __init__(self, name, channel_type, parent=None):
        super().__init__(parent)
        self.name = name
        self.type = channel_type  # "text" or "voice"
        
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        icon = "💬" if channel_type == "text" else "🔊"
        self.icon_label = QLabel(icon)
        self.icon_label.setStyleSheet("font-size: 16px;")
        
        self.name_label = QLabel(name)
        self.name_label.setStyleSheet("color: #aaaaaa;")
        
        layout.addWidget(self.icon_label)
        layout.addWidget(self.name_label)
        layout.addStretch()
        
        self.setLayout(layout)
        self.setStyleSheet("""
            QWidget {
                background: transparent;
                padding: 5px;
                border-radius: 5px;
            }
            QWidget:hover {
                background: #3a3a4a;
            }
        """)

class ServerWidget(QWidget):
    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.name = name
        self.channels = []
        self.is_expanded = False
        self.setup_ui()
        
    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Server header with expand button
        self.header = QPushButton("▶ " + self.name)
        self.header.setStyleSheet("""
            QPushButton {
                background: #2c2c3c;
                color: white;
                text-align: left;
                padding: 10px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                margin-bottom: 5px;
            }
            QPushButton:hover {
                background: #3a3a4a;
            }
        """)
        self.header.clicked.connect(self.toggle_expand)
        
        # Channels container (initially hidden)
        self.channels_container = QWidget()
        self.channels_layout = QVBoxLayout()
        self.channels_layout.setContentsMargins(15, 5, 5, 5)
        self.channels_layout.setSpacing(5)
        self.channels_container.setLayout(self.channels_layout)
        self.channels_container.hide()
        
        self.layout.addWidget(self.header)
        self.layout.addWidget(self.channels_container)
        
        # Add default channels
        self.add_channel("general", "text")
        self.add_channel("General Voice", "voice")
    
    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        self.channels_container.setVisible(self.is_expanded)
        # Update arrow icon
        if self.is_expanded:
            self.header.setText("▼ " + self.name)
        else:
            self.header.setText("▶ " + self.name)
    
    def add_channel(self, name, channel_type):
        channel = ServerChannelWidget(name, channel_type, self)
        self.channels.append(channel)
        self.channels_layout.addWidget(channel)

class ChatApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_data()
        self.setup_media()
        self.setup_ui()
        self.setup_connections()
        
    def setup_data(self):
        self.saved_messages = [
            (True, "Это мои сохранённые заметки."),
            (True, "Можно отправлять текст, смайлики, фото и видео."),
        ]

        self.chats_data = {
            "🟢 Alex": [
                (False, "Привет! Как дела?"),
                (True, "Привет, всё отлично! Ты как?"),
                (False, "Тоже хорошо, спасибо!"),
                (False, "Посмотри это фото!", "photo:example_photo.jpg"),
            ],
            "🟡 Jordan": [
                (False, "Ты сегодня будешь на стриме?"),
                (True, "Да, в 8 вечера."),
            ],
            "🔴 Maria": [
                (False, "Отправила тебе фото.", "photo:example_photo2.jpg"),
                (True, "Классное фото, спасибо!"),
            ],
        }

        # Store actual image paths for demo
        self.media_files = {
            "example_photo.jpg": os.path.abspath("example_photo.jpg"),
            "example_photo2.jpg": os.path.abspath("example_photo2.jpg")
        }

        self.friends_data = [
            {"name": "Alex", "status": "Playing Valorant", "online": True},
            {"name": "Jordan", "status": "Online", "online": True},
            {"name": "Maria", "status": "In Game", "online": True},
            {"name": "Chris", "status": "Offline", "online": False},
        ]

        self.servers = [
            {"name": "Gaming Hub", "channels": [
                {"name": "general", "type": "text"},
                {"name": "General Voice", "type": "voice"}
            ]},
            {"name": "Art Community", "channels": [
                {"name": "general", "type": "text"},
                {"name": "General Voice", "type": "voice"}
            ]}
        ]

        self.filtered_friends_data = self.friends_data.copy()
        self.current_chat = None
        self.in_call = False
        self.call_duration = 0
        self.mic_muted = False
        self.camera_off = False

    def setup_ui(self):
        self.setWindowTitle("DUMP Messenger")
        self.setGeometry(100, 100, 1280, 800)
        self.setStyleSheet("""
            background-color: #1f1f2a;
            color: #eeeeee;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        """)
        
        self.create_sidebar()
        self.create_top_bar()
        self.create_pages()
        self.create_right_sidebar()
        
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.top_bar)
        
        content_layout = QHBoxLayout()
        content_layout.addWidget(self.sidebar_widget)
        content_layout.addWidget(self.pages)
        content_layout.addWidget(self.right_sidebar)
        
        main_layout.addLayout(content_layout)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        self.sidebar_buttons[0].setChecked(True)
        self.switch_page(0)

    def setup_media(self):
        self.media_player = QMediaPlayer()
        self.video_widget = QVideoWidget()
        self.media_player.setVideoOutput(self.video_widget)
        
        self.call_timer = QTimer()
        self.call_timer.timeout.connect(self.update_call_time)
        self.current_call_type = None

    def setup_connections(self):
        if hasattr(self, 'chat_input'):
            self.chat_input.returnPressed.connect(self.send_chat_message)
        if hasattr(self, 'send_btn'):
            self.send_btn.clicked.connect(self.send_chat_message)
        if hasattr(self, 'photo_btn'):
            self.photo_btn.clicked.connect(self.attach_photo)
        if hasattr(self, 'emoji_btn'):
            self.emoji_btn.clicked.connect(self.show_emoji_picker)
        if hasattr(self, 'audio_call_btn'):
            self.audio_call_btn.clicked.connect(lambda: self.start_call('audio'))
        if hasattr(self, 'video_call_btn'):
            self.video_call_btn.clicked.connect(lambda: self.start_call('video'))
        if hasattr(self, 'end_call_btn'):
            self.end_call_btn.clicked.connect(self.end_call)
        if hasattr(self, 'saved_send_btn'):
            self.saved_send_btn.clicked.connect(self.send_saved_message)
        if hasattr(self, 'saved_input'):
            self.saved_input.returnPressed.connect(self.send_saved_message)
        if hasattr(self, 'saved_emoji_btn'):
            self.saved_emoji_btn.clicked.connect(self.show_emoji_picker)
        if hasattr(self, 'saved_photo_btn'):
            self.saved_photo_btn.clicked.connect(self.attach_photo_saved)
        if hasattr(self, 'friends_search'):
            self.friends_search.textChanged.connect(self.filter_friends)
        if hasattr(self, 'contact_list'):
            self.contact_list.currentItemChanged.connect(self.load_chat)
        if hasattr(self, 'new_server_btn'):
            self.new_server_btn.clicked.connect(self.create_new_server)
        if hasattr(self, 'friends_list_widget'):
            self.friends_list_widget.itemClicked.connect(self.friend_item_clicked)
        if hasattr(self, 'mic_btn'):
            self.mic_btn.clicked.connect(self.toggle_mic)
        if hasattr(self, 'camera_btn'):
            self.camera_btn.clicked.connect(self.toggle_camera)

    def create_sidebar(self):
        self.sidebar_widget = QWidget()
        self.sidebar_widget.setStyleSheet("background-color: #13131a;")
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(0, 20, 0, 20)
        sidebar_layout.setSpacing(15)

        buttons = [
            ("My Profile", "profile.png", 0),
            ("Chats", "chat.png", 1),
            ("Servers", "server.png", 2),
            ("Friends", "friends.png", 3),
            ("Saved Messages", "saved.png", 4),
        ]

        self.sidebar_buttons = []
        for text, icon, idx in buttons:
            btn = QPushButton()
            btn.setIcon(QIcon(f"icons/{icon}"))
            btn.setIconSize(QSize(28, 28))
            btn.setFixedSize(48, 48)
            btn.setStyleSheet(self.button_style())
            btn.setToolTip(text)
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, i=idx: self.switch_page(i))
            sidebar_layout.addWidget(btn)
            self.sidebar_buttons.append(btn)

        sidebar_layout.addStretch()
        self.settings_btn = QPushButton()
        self.settings_btn.setIcon(QIcon("icons/settings.png"))
        self.settings_btn.setIconSize(QSize(28, 28))
        self.settings_btn.setFixedSize(48, 48)
        self.settings_btn.setStyleSheet(self.button_style())
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.setCheckable(True)
        self.settings_btn.clicked.connect(lambda: self.switch_page(5))
        sidebar_layout.addWidget(self.settings_btn)

        self.sidebar_widget.setLayout(sidebar_layout)
        self.sidebar_widget.setFixedWidth(64)

    def create_top_bar(self):
        self.top_bar = QWidget()
        self.top_bar.setFixedHeight(60)
        self.top_bar.setStyleSheet("background-color: #111118;")
        
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(20, 0, 20, 0)
        
        self.logo = QLabel()
        self.logo.setPixmap(QPixmap("icons/logo.png").scaled(40, 40))
        
        self.title = QLabel("DUMP")
        self.title.setStyleSheet("color: #d8ff56; font-size: 28px; font-weight: 900;")
        
        top_layout.addWidget(self.logo)
        top_layout.addWidget(self.title)
        top_layout.addStretch()
        
        self.top_bar.setLayout(top_layout)

    def create_pages(self):
        self.pages = QStackedWidget()
        self.pages.addWidget(self.create_profile_page())
        self.pages.addWidget(self.create_chats_page())
        self.pages.addWidget(self.create_servers_page())
        self.pages.addWidget(self.create_friends_page())
        self.pages.addWidget(self.create_saved_page())
        self.pages.addWidget(self.create_settings_page())
        self.pages.addWidget(self.create_signup_page())
        self.pages.addWidget(self.create_call_page())

    def create_right_sidebar(self):
        self.right_sidebar = QWidget()
        self.right_sidebar.setStyleSheet("background-color: #13131a;")
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Online Friends
        online_frame = QWidget()
        online_frame.setStyleSheet("background: #1a1a26; border-radius: 12px; padding: 15px;")
        online_layout = QVBoxLayout()
        
        online_title = QLabel("Online Friends")
        online_title.setStyleSheet("font-weight: bold; font-size: 16px; color: #d8ff56; margin-bottom: 10px;")
        
        online_layout.addWidget(online_title)
        
        online_friends = [f for f in self.friends_data if f["online"]]
        for friend in online_friends:
            friend_widget = QWidget()
            friend_layout = QHBoxLayout()
            
            avatar = QLabel(friend["name"][0])
            avatar.setFixedSize(32, 32)
            avatar.setAlignment(Qt.AlignCenter)
            avatar.setStyleSheet("""
                background-color: #d8ff56;
                color: black;
                border-radius: 16px;
                font-weight: bold;
                font-size: 16px;
            """)
            
            info_widget = QWidget()
            info_layout = QVBoxLayout()
            info_layout.setContentsMargins(10, 0, 0, 0)
            
            name_label = QLabel(friend["name"])
            name_label.setStyleSheet("font-weight: bold; color: white;")
            
            status_label = QLabel(friend["status"])
            status_label.setStyleSheet("color: #aaaaaa; font-size: 14px;")
            
            info_layout.addWidget(name_label)
            info_layout.addWidget(status_label)
            info_widget.setLayout(info_layout)
            
            friend_layout.addWidget(avatar)
            friend_layout.addWidget(info_widget)
            friend_layout.addStretch()
            
            friend_widget.setLayout(friend_layout)
            online_layout.addWidget(friend_widget)
        
        online_frame.setLayout(online_layout)
        layout.addWidget(online_frame)
        
        # Friends in game
        game_frame = QWidget()
        game_frame.setStyleSheet("background: #1a1a26; border-radius: 12px; padding: 15px;")
        game_layout = QVBoxLayout()
        
        game_title = QLabel("Friends in game")
        game_title.setStyleSheet("font-weight: bold; font-size: 16px; color: #d8ff56; margin-bottom: 10px;")
        
        games = [
            ("Alex", "Counter Strike 2"),
            ("Maria", "Dota 2")
        ]
        
        game_layout.addWidget(game_title)
        for user, game in games:
            label = QLabel(f"🟢 {user} играет в {game}")
            label.setStyleSheet("padding: 5px 0;")
            game_layout.addWidget(label)
        
        game_frame.setLayout(game_layout)
        layout.addWidget(game_frame)
        layout.addStretch()
        
        self.right_sidebar.setLayout(layout)
        self.right_sidebar.setFixedWidth(280)

    def create_profile_page(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("User Profile")
        title.setStyleSheet("font-size: 28px; color: #d8ff56; font-weight: 900;")
        
        avatar = QLabel()
        avatar.setPixmap(QPixmap("icons/avatar.png").scaled(120, 120))
        avatar.setStyleSheet("border-radius: 60px;")
        
        info = QLabel("Helena Hills\nActive 20m ago")
        info.setStyleSheet("font-size: 16px;")
        
        quote = QLabel("Тут короче какая-то офигеть глубокомысленная цитата")
        quote.setStyleSheet("font-style: italic; color: #aaaaaa; margin-top: 20px;")
        
        layout.addWidget(title)
        layout.addWidget(avatar, alignment=Qt.AlignCenter)
        layout.addWidget(info, alignment=Qt.AlignCenter)
        layout.addWidget(quote)
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget

    def create_chats_page(self):
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.contact_list = QListWidget()
        self.contact_list.setFixedWidth(280)
        self.contact_list.setStyleSheet("""
            QListWidget {
                background-color: #1a1a26;
                border: none;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #2e2e40;
            }
            QListWidget::item:selected {
                background-color: #d8ff56;
                color: #000000;
            }
        """)
        
        for user in self.chats_data.keys():
            self.contact_list.addItem(QListWidgetItem(user))
        
        chat_area = QVBoxLayout()
        chat_area.setContentsMargins(0, 0, 0, 0)
        
        self.chat_header = QWidget()
        self.chat_header.setStyleSheet("background-color: #1a1a26;")
        header_layout = QHBoxLayout()
        
        self.chat_title = QLabel("Select a chat")
        self.chat_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #d8ff56;")
        
        header_layout.addWidget(self.chat_title)
        header_layout.addStretch()
        
        self.audio_call_btn = QPushButton()
        self.audio_call_btn.setIcon(QIcon("icons/call.png"))
        self.audio_call_btn.setIconSize(QSize(24, 24))
        self.audio_call_btn.setFixedSize(36, 36)
        self.audio_call_btn.setStyleSheet("background: transparent; border: none;")
        self.audio_call_btn.setToolTip("Audio Call")
        self.audio_call_btn.hide()
        
        self.video_call_btn = QPushButton()
        self.video_call_btn.setIcon(QIcon("icons/video.png"))
        self.video_call_btn.setIconSize(QSize(24, 24))
        self.video_call_btn.setFixedSize(36, 36)
        self.video_call_btn.setStyleSheet("background: transparent; border: none;")
        self.video_call_btn.setToolTip("Video Call")
        self.video_call_btn.hide()
        
        header_layout.addWidget(self.audio_call_btn)
        header_layout.addWidget(self.video_call_btn)
        self.chat_header.setLayout(header_layout)

        self.chat_display = QTextBrowser()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            background-color: #2c2c3c;
            color: white;
            border: none;
            padding: 15px;
            font-size: 14px;
        """)
        self.chat_display.setOpenExternalLinks(True)

        input_widget = QWidget()
        input_widget.setStyleSheet("background-color: #1a1a26; padding: 10px;")
        input_layout = QHBoxLayout()
        
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Enter your message...")
        self.chat_input.setStyleSheet("""
            background-color: #2c2c3c;
            color: white;
            border: none;
            border-radius: 18px;
            padding: 10px 15px;
            font-size: 14px;
        """)
        self.chat_input.setDisabled(True)
        
        self.emoji_btn = QPushButton("😀")
        self.emoji_btn.setStyleSheet("font-size: 18px; background: transparent;")
        
        self.photo_btn = QPushButton()
        self.photo_btn.setIcon(QIcon("icons/photo.png"))
        self.photo_btn.setIconSize(QSize(24, 24))
        self.photo_btn.setStyleSheet("background: transparent; border: none;")
        
        self.send_btn = QPushButton("Send")
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #d8ff56;
                color: black;
                border: none;
                border-radius: 18px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ecff87;
            }
        """)
        
        input_layout.addWidget(self.chat_input)
        input_layout.addWidget(self.emoji_btn)
        input_layout.addWidget(self.photo_btn)
        input_layout.addWidget(self.send_btn)
        input_widget.setLayout(input_layout)
        
        chat_area.addWidget(self.chat_header)
        chat_area.addWidget(self.chat_display)
        chat_area.addWidget(input_widget)
        
        layout.addWidget(self.contact_list)
        layout.addLayout(chat_area)
        
        widget.setLayout(layout)
        return widget

    def create_servers_page(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        header = QHBoxLayout()
        title = QLabel("Servers")
        title.setStyleSheet("font-size: 24px; color: #d8ff56; font-weight: 900;")
        
        self.new_server_btn = QPushButton("New server")
        self.new_server_btn.setStyleSheet("""
            QPushButton {
                background-color: #d8ff56;
                color: black;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ecff87;
            }
        """)
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.new_server_btn)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        self.servers_container_layout = QVBoxLayout()
        self.servers_container_layout.setSpacing(10)
        
        for server in self.servers:
            server_widget = ServerWidget(server["name"])
            for channel in server["channels"]:
                server_widget.add_channel(channel["name"], channel["type"])
            self.servers_container_layout.addWidget(server_widget)
        
        container.setLayout(self.servers_container_layout)
        scroll.setWidget(container)
        
        layout.addLayout(header)
        layout.addWidget(scroll)
        
        widget.setLayout(layout)
        return widget

    def create_friends_page(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        header = QHBoxLayout()
        title = QLabel("Friends")
        title.setStyleSheet("font-size: 24px; color: #d8ff56; font-weight: 900;")
        
        self.friends_search = QLineEdit()
        self.friends_search.setPlaceholderText("Search friends...")
        self.friends_search.setStyleSheet("""
            background-color: #2c2c3c;
            color: white;
            border: none;
            border-radius: 18px;
            padding: 10px 15px;
            font-size: 14px;
        """)
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.friends_search)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(10)
        
        self.friends_list_widget = QListWidget()
        self.friends_list_widget.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                font-size: 14px;
            }
            QListWidget::item {
                height: 70px;
                background: #2c2c3c;
                border-radius: 8px;
                margin-bottom: 8px;
            }
            QListWidget::item:hover {
                background: #3a3a4a;
            }
            QListWidget::item:selected {
                background: #3a3a4a;
                border-left: 4px solid #d8ff56;
            }
        """)
        
        self.update_friends_list()
        
        container_layout.addWidget(self.friends_list_widget)
        container.setLayout(container_layout)
        scroll.setWidget(container)
        
        layout.addLayout(header)
        layout.addWidget(scroll)
        
        widget.setLayout(layout)
        return widget

    def create_saved_page(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("Saved Messages")
        title.setStyleSheet("font-size: 24px; color: #d8ff56; font-weight: 900; margin-bottom: 20px;")
        
        self.saved_display = QTextEdit()
        self.saved_display.setReadOnly(True)
        self.saved_display.setStyleSheet("""
            background-color: #2c2c3c;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 15px;
            font-size: 14px;
        """)
        
        for is_me, text in self.saved_messages:
            if is_me:
                self.saved_display.append(f"<p style='color:white; background:#3a3a4a; padding:8px; border-radius:8px; margin:5px;'>{text}</p>")
    
        input_widget = QWidget()
        input_widget.setStyleSheet("background-color: #1a1a26; padding: 10px; border-radius: 8px;")
        input_layout = QHBoxLayout()
        
        self.saved_input = QLineEdit()
        self.saved_input.setPlaceholderText("Add new saved message...")
        self.saved_input.setStyleSheet("""
            background-color: #2c2c3c;
            color: white;
            border: none;
            border-radius: 18px;
            padding: 10px 15px;
            font-size: 14px;
        """)
        
        self.saved_emoji_btn = QPushButton("😀")
        self.saved_emoji_btn.setStyleSheet("font-size: 18px; background: transparent;")
        
        self.saved_photo_btn = QPushButton()
        self.saved_photo_btn.setIcon(QIcon("icons/photo.png"))
        self.saved_photo_btn.setIconSize(QSize(24, 24))
        self.saved_photo_btn.setStyleSheet("background: transparent; border: none;")
        
        self.saved_send_btn = QPushButton("Save")
        self.saved_send_btn.setStyleSheet("""
            QPushButton {
                background-color: #d8ff56;
                color: black;
                border: none;
                border-radius: 18px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ecff87;
            }
        """)
        
        input_layout.addWidget(self.saved_input)
        input_layout.addWidget(self.saved_emoji_btn)
        input_layout.addWidget(self.saved_photo_btn)
        input_layout.addWidget(self.saved_send_btn)
        input_widget.setLayout(input_layout)
        
        layout.addWidget(title)
        layout.addWidget(self.saved_display)
        layout.addWidget(input_widget)
        
        widget.setLayout(layout)
        return widget

    def create_settings_page(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("Settings")
        title.setStyleSheet("font-size: 24px; color: #d8ff56; font-weight: 900; margin-bottom: 20px;")
        
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: #2c2c3c;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: #1a1a26;
                color: white;
                padding: 8px 16px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #d8ff56;
                color: black;
            }
        """)
        
        # Account Tab
        account_tab = QWidget()
        account_layout = QVBoxLayout()
        
        avatar_group = QWidget()
        avatar_layout = QHBoxLayout()
        
        avatar_label = QLabel()
        avatar_label.setPixmap(QPixmap("icons/avatar.png").scaled(80, 80))
        avatar_label.setStyleSheet("border-radius: 40px;")
        
        avatar_btn = QPushButton("Change Avatar")
        avatar_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a4a;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #4a4a5a;
            }
        """)
        
        avatar_layout.addWidget(avatar_label)
        avatar_layout.addWidget(avatar_btn)
        avatar_layout.addStretch()
        avatar_group.setLayout(avatar_layout)
        
        form = QWidget()
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(15)
        
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("Enter your name")
        name_edit.setStyleSheet("""
            background-color: #3a3a4a;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px;
        """)
        
        nickname_edit = QLineEdit()
        nickname_edit.setPlaceholderText("Enter your nickname")
        nickname_edit.setStyleSheet("""
            background-color: #3a3a4a;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px;
        """)
        
        email_edit = QLineEdit()
        email_edit.setPlaceholderText("Enter your email")
        email_edit.setStyleSheet("""
            background-color: #3a3a4a;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px;
        """)
        
        save_btn = QPushButton("Save Changes")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #d8ff56;
                color: black;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ecff87;
            }
        """)
        
        form_layout.addRow("Name:", name_edit)
        form_layout.addRow("Nickname:", nickname_edit)
        form_layout.addRow("Email:", email_edit)
        form_layout.addRow(save_btn)
        form.setLayout(form_layout)
        
        account_layout.addWidget(avatar_group)
        account_layout.addWidget(form)
        account_layout.addStretch()
        account_tab.setLayout(account_layout)
        
        # Privacy Tab
        privacy_tab = QWidget()
        privacy_layout = QVBoxLayout()
        
        privacy_group = QWidget()
        privacy_group_layout = QVBoxLayout()
        privacy_group_layout.setSpacing(15)
        
        online_status = QCheckBox("Show online status")
        online_status.setStyleSheet("color: white;")
        online_status.setChecked(True)
        
        activity = QCheckBox("Show current activity")
        activity.setStyleSheet("color: white;")
        activity.setChecked(True)
        
        last_seen = QCheckBox("Show last seen time")
        last_seen.setStyleSheet("color: white;")
        last_seen.setChecked(True)
        
        privacy_group_layout.addWidget(online_status)
        privacy_group_layout.addWidget(activity)
        privacy_group_layout.addWidget(last_seen)
        privacy_group.setLayout(privacy_group_layout)
        
        privacy_layout.addWidget(privacy_group)
        privacy_layout.addStretch()
        privacy_tab.setLayout(privacy_layout)
        
        tabs.addTab(account_tab, "Account")
        tabs.addTab(privacy_tab, "Privacy")
        
        layout.addWidget(title)
        layout.addWidget(tabs)
        
        widget.setLayout(layout)
        return widget

    def create_signup_page(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(100, 50, 100, 50)
        
        title = QLabel("Create Account")
        title.setStyleSheet("font-size: 28px; color: #d8ff56; font-weight: 900; text-align: center; margin-bottom: 30px;")
        
        form = QWidget()
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(15)
        
        fields = [
            ("Username:", QLineEdit()),
            ("Nickname:", QLineEdit()),
            ("Email:", QLineEdit()),
            ("Password:", QLineEdit()),
            ("Confirm Password:", QLineEdit())
        ]
        
        for label_text, field in fields:
            label = QLabel(label_text)
            label.setStyleSheet("color: white; font-size: 16px;")
            
            if isinstance(field, QLineEdit):
                if "Password" in label_text:
                    field.setEchoMode(QLineEdit.Password)
                field.setStyleSheet("""
                    background-color: #2c2c3c;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 15px;
                    font-size: 14px;
                """)
            
            form_layout.addRow(label, field)
        
        signup_btn = QPushButton("Sign Up")
        signup_btn.setStyleSheet("""
            QPushButton {
                background-color: #d8ff56;
                color: black;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-weight: bold;
                font-size: 16px;
                margin-top: 20px;
            }
            QPushButton:hover {
                background-color: #ecff87;
            }
        """)
        
        form_layout.addRow(signup_btn)
        form.setLayout(form_layout)
        
        layout.addWidget(title)
        layout.addWidget(form)
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget

    def create_call_page(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.video_layout = QVBoxLayout()
        self.video_layout.setContentsMargins(0, 0, 0, 0)
        
        # Video widget takes most space
        self.video_widget.setStyleSheet("background-color: black;")
        self.video_layout.addWidget(self.video_widget, 1)
        
        # Call info overlay
        call_info = QWidget()
        call_info.setStyleSheet("background-color: rgba(0,0,0,0.7);")
        call_info_layout = QVBoxLayout()
        
        self.call_status_label = QLabel("Call in progress")
        self.call_status_label.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        self.call_status_label.setAlignment(Qt.AlignCenter)
        
        self.call_time_label = QLabel("00:00")
        self.call_time_label.setStyleSheet("color: white; font-size: 16px;")
        self.call_time_label.setAlignment(Qt.AlignCenter)
        
        call_info_layout.addWidget(self.call_status_label)
        call_info_layout.addWidget(self.call_time_label)
        call_info.setLayout(call_info_layout)
        
        # Controls panel at bottom
        controls = QWidget()
        controls.setStyleSheet("background-color: rgba(0,0,0,0.7);")
        controls_layout = QHBoxLayout()
        
        # Mic control
        self.mic_btn = QPushButton()
        self.mic_btn.setIcon(QIcon("icons/mic_on.png"))
        self.mic_btn.setIconSize(QSize(32, 32))
        self.mic_btn.setFixedSize(48, 48)
        self.mic_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a4a;
                border-radius: 24px;
            }
            QPushButton:hover {
                background-color: #4a4a5a;
            }
        """)
        self.mic_btn.setToolTip("Mute microphone")
        
        # Camera control
        self.camera_btn = QPushButton()
        self.camera_btn.setIcon(QIcon("icons/camera_on.png"))
        self.camera_btn.setIconSize(QSize(32, 32))
        self.camera_btn.setFixedSize(48, 48)
        self.camera_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a4a;
                border-radius: 24px;
            }
            QPushButton:hover {
                background-color: #4a4a5a;
            }
        """)
        self.camera_btn.setToolTip("Turn off camera")
        
        # End call button
        self.end_call_btn = QPushButton()
        self.end_call_btn.setIcon(QIcon("icons/call.png"))
        self.end_call_btn.setIconSize(QSize(48, 48))
        self.end_call_btn.setFixedSize(64, 64)
        self.end_call_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff5555;
                border-radius: 32px;
            }
            QPushButton:hover {
                background-color: #ff7777;
            }
        """)
        self.end_call_btn.setToolTip("End call")
        
        # Screen share button
        self.screen_share_btn = QPushButton()
        self.screen_share_btn.setIcon(QIcon("icons/screen_share.png"))
        self.screen_share_btn.setIconSize(QSize(32, 32))
        self.screen_share_btn.setFixedSize(48, 48)
        self.screen_share_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a4a;
                border-radius: 24px;
            }
            QPushButton:hover {
                background-color: #4a4a5a;
            }
        """)
        self.screen_share_btn.setToolTip("Share screen")
        
        controls_layout.addStretch()
        controls_layout.addWidget(self.mic_btn)
        controls_layout.addWidget(self.camera_btn)
        controls_layout.addWidget(self.end_call_btn)
        controls_layout.addWidget(self.screen_share_btn)
        controls_layout.addStretch()
        controls.setLayout(controls_layout)
        
        self.video_layout.addWidget(call_info)
        self.video_layout.addWidget(controls)
        
        widget.setLayout(self.video_layout)
        return widget

    def load_chat(self, current):
        if current:
            user = current.text()
            self.current_chat = user
            self.chat_title.setText(user)
            self.chat_display.clear()
            self.chat_input.setEnabled(True)
            
            self.audio_call_btn.show()
            self.video_call_btn.show()
            
            for is_me, *content in self.chats_data[user]:
                if len(content) == 1:
                    self.display_message(user, is_me, content[0])
                else:
                    # Handle media files
                    media_type, filename = content[1].split(":")
                    if media_type == "photo":
                        self.display_photo_message(user, is_me, filename)
            
            self.chat_display.moveCursor(QTextCursor.End)
        else:
            self.chat_title.setText("Select a chat")
            self.chat_display.clear()
            self.chat_input.setDisabled(True)
            self.audio_call_btn.hide()
            self.video_call_btn.hide()
            self.current_chat = None

    def display_message(self, user, is_me, text):
        if is_me:
            self.chat_display.append(
                f"<p style='color:black; background:#d8ff56; padding:6px; border-radius:8px; max-width:70%; float:right; clear:both;'>"
                f"<b>You:</b> {text}</p>")
        else:
            self.chat_display.append(
                f"<p style='color:#d8ff56; font-weight: 700; margin-bottom: 2px; max-width:70%; float:left; clear:both;'>{user}</p>")
            self.chat_display.append(
                f"<p style='color:#eeeeee; background:#3a3a4a; padding:6px; border-radius:8px; max-width:70%; float:left; clear:both; margin-top:0;'>{text}</p>")

    def display_photo_message(self, user, is_me, filename):
        if filename in self.media_files:
            filepath = self.media_files[filename]
            if is_me:
                self.chat_display.append(
                    f"<p style='color:black; background:#d8ff56; padding:6px; border-radius:8px; max-width:70%; float:right; clear:both;'>"
                    f"<b>You:</b> <a href='{filepath}'><img src='{filepath}' width='200' /></a></p>")
            else:
                self.chat_display.append(
                    f"<p style='color:#d8ff56; font-weight: 700; margin-bottom: 2px; max-width:70%; float:left; clear:both;'>{user}</p>")
                self.chat_display.append(
                    f"<p style='color:#eeeeee; background:#3a3a4a; padding:6px; border-radius:8px; max-width:70%; float:left; clear:both; margin-top:0;'>"
                    f"<a href='{filepath}'><img src='{filepath}' width='200' /></a></p>")
        else:
            self.display_message(user, is_me, f"📷 Photo: {filename}")

    def send_chat_message(self):
        text = self.chat_input.text().strip()
        if text and self.current_chat:
            self.chats_data.setdefault(self.current_chat, []).append((True, text))
            self.display_message(self.current_chat, True, text)
            self.chat_input.clear()

    def send_saved_message(self):
        text = self.saved_input.text().strip()
        if text:
            self.saved_messages.append((True, text))
            self.saved_display.append(f"<p style='color:white; background:#3a3a4a; padding:8px; border-radius:8px; margin:5px;'>{text}</p>")
            self.saved_input.clear()

    def attach_photo(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Image", 
            "", 
            "Images (*.png *.jpg *.jpeg)"
        )
        
        if file_path and self.current_chat:
            filename = os.path.basename(file_path)
            self.media_files[filename] = file_path
            self.chats_data.setdefault(self.current_chat, []).append((True, f"photo:{filename}"))
            self.display_photo_message(
                self.current_chat, 
                True, 
                filename
            )

    def attach_photo_saved(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Image", 
            "", 
            "Images (*.png *.jpg *.jpeg)"
        )
        
        if file_path:
            filename = os.path.basename(file_path)
            self.media_files[filename] = file_path
            self.saved_messages.append((True, f"📷 Photo: {filename}"))
            self.saved_display.append(
                f"<p style='color:white; background:#3a3a4a; padding:8px; border-radius:8px; margin:5px;'>"
                f"<a href='{file_path}'><img src='{file_path}' width='200' /></a></p>")

    def show_emoji_picker(self):
        picker = EmojiPicker(self)
        picker.exec_()

    def insert_emoji(self, emoji):
        if self.pages.currentIndex() == 1 and hasattr(self, "chat_input") and self.chat_input.isEnabled():
            self.chat_input.insert(emoji)
            self.chat_input.setFocus()
        elif self.pages.currentIndex() == 4 and hasattr(self, "saved_input"):
            self.saved_input.insert(emoji)
            self.saved_input.setFocus()

    def start_call(self, call_type):
        if not self.current_chat:
            return
            
        self.current_call_type = call_type
        self.in_call = True
        self.call_duration = 0
        self.call_timer.start(1000)
        
        self.pages.setCurrentIndex(7)
        self.call_status_label.setText(f"{call_type.capitalize()} call with {self.current_chat}")
        self.call_time_label.setText("00:00")
        
        if call_type == 'video':
            self.video_layout.insertWidget(0, self.video_widget)
            self.camera_btn.show()
        else:
            self.camera_btn.hide()

    def end_call(self):
        self.call_timer.stop()
        self.in_call = False
        self.pages.setCurrentIndex(1)
        
        if self.current_call_type == 'video':
            self.video_layout.removeWidget(self.video_widget)

    def update_call_time(self):
        self.call_duration += 1
        minutes = self.call_duration // 60
        seconds = self.call_duration % 60
        self.call_time_label.setText(f"{minutes:02d}:{seconds:02d}")

    def toggle_mic(self):
        self.mic_muted = not self.mic_muted
        if self.mic_muted:
            self.mic_btn.setIcon(QIcon("icons/mic_off.png"))
            self.mic_btn.setToolTip("Unmute microphone")
        else:
            self.mic_btn.setIcon(QIcon("icons/mic_on.png"))
            self.mic_btn.setToolTip("Mute microphone")

    def toggle_camera(self):
        self.camera_off = not self.camera_off
        if self.camera_off:
            self.camera_btn.setIcon(QIcon("icons/camera_off.png"))
            self.camera_btn.setToolTip("Turn on camera")
        else:
            self.camera_btn.setIcon(QIcon("icons/camera_on.png"))
            self.camera_btn.setToolTip("Turn off camera")

    def friend_item_clicked(self, item):
        # Find which friend was clicked
        widget = self.friends_list_widget.itemWidget(item)
        if widget:
            # Find the name label in the widget's layout
            for i in range(widget.layout().count()):
                child = widget.layout().itemAt(i).widget()
                if isinstance(child, QWidget):
                    for sub_child in child.children():
                        if isinstance(sub_child, QLabel) and sub_child.text() in [f["name"] for f in self.friends_data]:
                            friend_name = sub_child.text()
                            # Find or create chat with this friend
                            chat_key = f"🟢 {friend_name}"  # Simplified for demo
                            if chat_key not in self.chats_data:
                                self.chats_data[chat_key] = []
                            
                            # Switch to chats page and select this chat
                            self.switch_page(1)  # Chats page
                            # Find and select the chat in contact list
                            for i in range(self.contact_list.count()):
                                if self.contact_list.item(i).text() == chat_key:
                                    self.contact_list.setCurrentRow(i)
                                    break
                            return

    def update_friends_list(self):
        self.friends_list_widget.clear()
        for friend in self.filtered_friends_data:
            item = QListWidgetItem()
            widget = QWidget()
            layout = QHBoxLayout()
            layout.setContentsMargins(10, 5, 10, 5)
            
            # Avatar with online status indicator
            avatar_container = QWidget()
            avatar_layout = QVBoxLayout()
            avatar_layout.setContentsMargins(0, 0, 0, 0)
            avatar_layout.setAlignment(Qt.AlignCenter)
            
            avatar = QLabel(friend["name"][0])
            avatar.setFixedSize(40, 40)
            avatar.setAlignment(Qt.AlignCenter)
            avatar.setStyleSheet(f"""
                background-color: {'#d8ff56' if friend["online"] else '#aaaaaa'};
                color: black;
                border-radius: 20px;
                font-weight: bold;
                font-size: 18px;
            """)
            
            # Online status dot
            status_dot = QLabel()
            status_dot.setFixedSize(10, 10)
            status_dot.setStyleSheet(f"""
                background-color: {'#00ff00' if friend["online"] else '#888888'};
                border-radius: 5px;
            """)
            
            avatar_layout.addWidget(avatar)
            avatar_layout.addWidget(status_dot, 0, Qt.AlignRight)
            avatar_container.setLayout(avatar_layout)
            
            # Friend info
            info_widget = QWidget()
            info_layout = QVBoxLayout()
            info_layout.setContentsMargins(10, 0, 0, 0)
            info_layout.setSpacing(5)
            
            name_label = QLabel(friend["name"])
            name_label.setStyleSheet("""
                font-weight: bold; 
                font-size: 16px;
                color: white;
            """)
            
            status_label = QLabel(friend["status"])
            status_label.setStyleSheet("""
                color: #aaaaaa; 
                font-size: 14px;
            """)
            
            info_layout.addWidget(name_label)
            info_layout.addWidget(status_label)
            info_widget.setLayout(info_layout)
            
            layout.addWidget(avatar_container)
            layout.addWidget(info_widget)
            layout.addStretch()
            
            widget.setLayout(layout)
            item.setSizeHint(widget.sizeHint())
            self.friends_list_widget.addItem(item)
            self.friends_list_widget.setItemWidget(item, widget)

    def filter_friends(self):
        search_text = self.friends_search.text().lower()
        if not search_text:
            self.filtered_friends_data = self.friends_data.copy()
        else:
            self.filtered_friends_data = [
                friend for friend in self.friends_data 
                if search_text in friend["name"].lower() or search_text in friend["status"].lower()
            ]
        self.update_friends_list()

    def create_new_server(self):
        name, ok = QInputDialog.getText(
            self, 
            "Create New Server", 
            "Enter server name:",
            QLineEdit.Normal,
            ""
        )
        
        if ok and name:
            new_server = {
                "name": name,
                "channels": [
                    {"name": "general", "type": "text"},
                    {"name": "General Voice", "type": "voice"}
                ]
            }
            self.servers.append(new_server)
            
            # Add new server widget
            server_widget = ServerWidget(name)
            self.servers_container_layout.addWidget(server_widget)
            
            QMessageBox.information(
                self,
                "Server Created",
                f"Server '{name}' was successfully created with default channels!",
                QMessageBox.Ok
            )

    def switch_page(self, index):
        self.pages.setCurrentIndex(index)
        for i, btn in enumerate(self.sidebar_buttons):
            btn.setChecked(i == index)
        self.settings_btn.setChecked(index == 5)

    def button_style(self):
        return """
            QPushButton {
                background-color: transparent;
                border: none;
                color: #9ca3af;
            }
            QPushButton:hover {
                background-color: #2c2c3c;
                border-radius: 12px;
                color: #d8ff56;
            }
            QPushButton:checked {
                background-color: #d8ff56;
                color: black;
                border-radius: 12px;
            }
        """

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatApp()
    window.show()
    sys.exit(app.exec_())

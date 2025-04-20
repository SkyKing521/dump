import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLabel, QStackedWidget, QTextEdit,
    QFrame, QLineEdit, QPushButton, QScrollArea, QSizePolicy
)
from PyQt5.QtGui import QPixmap, QIcon, QTextCursor
from PyQt5.QtCore import Qt, QSize


class ChatApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("DUMP")
        self.setGeometry(100, 100, 1280, 800)
        self.setStyleSheet("""
            background-color: #1f1f2a;
            color: #eeeeee;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        """)

        # Инициализируем saved_messages ДО создания страниц
        self.saved_messages = [
            (True, "Это мои сохранённые заметки."),
            (True, "Можно отправлять текст, смайлики, фото и видео."),
        ]

        # --- Sidebar (Left)
        self.sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(0, 20, 0, 20)
        sidebar_layout.setSpacing(30)

        self.sidebar_buttons = []
        icons = [
            ("icons/profile.png", "My Profile"),
            ("icons/chat.png", "Chats"),
            ("icons/server.png", "Servers"),
            ("icons/friends.png", "Friends"),
            ("icons/saved.png", "Saved Messages"),
        ]

        for i, (icon_path, tooltip) in enumerate(icons):
            btn = QPushButton()
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(QSize(28, 28))
            btn.setFixedSize(48, 48)
            btn.setStyleSheet(self.button_style())
            btn.setCheckable(True)
            btn.setToolTip(tooltip)
            btn.clicked.connect(lambda checked, idx=i: self.switch_page(idx))
            sidebar_layout.addWidget(btn)
            self.sidebar_buttons.append(btn)

        sidebar_layout.addStretch()

        self.settings_button = QPushButton()
        self.settings_button.setIcon(QIcon("icons/settings.png"))
        self.settings_button.setIconSize(QSize(28, 28))
        self.settings_button.setFixedSize(48, 48)
        self.settings_button.setStyleSheet(self.button_style())
        self.settings_button.setCheckable(True)
        self.settings_button.setToolTip("Settings")
        self.settings_button.clicked.connect(lambda: self.switch_page(5))
        sidebar_layout.addWidget(self.settings_button)

        self.sidebar_widget.setLayout(sidebar_layout)
        self.sidebar_widget.setFixedWidth(64)

        # --- Right Sidebar (Friends Online)
        self.right_sidebar = self.create_right_sidebar()
        self.right_sidebar.setFixedWidth(280)

        # --- Top Bar
        self.top_bar = self.create_top_bar()

        # --- Pages
        self.pages = QStackedWidget()
        self.profile_page = self.create_profile_page()
        self.chats_page = self.create_chats_page()
        self.servers_page = self.create_servers_page()
        self.friends_page = self.create_friends_page()
        self.saved_page = self.create_saved_page()
        self.settings_page = self.create_settings_page()

        self.pages.addWidget(self.profile_page)
        self.pages.addWidget(self.chats_page)
        self.pages.addWidget(self.servers_page)
        self.pages.addWidget(self.friends_page)
        self.pages.addWidget(self.saved_page)
        self.pages.addWidget(self.settings_page)

        for btn in self.sidebar_buttons:
            btn.clicked.connect(self.uncheck_others)
        self.settings_button.clicked.connect(self.uncheck_others)

        # По умолчанию активна страница "My Profile"
        self.sidebar_buttons[0].setChecked(True)
        self.pages.setCurrentIndex(0)
        self.right_sidebar.setVisible(False)

        # --- Main Layout
        central_layout = QVBoxLayout()
        central_layout.addWidget(self.top_bar)

        content_layout = QHBoxLayout()
        content_layout.addWidget(self.sidebar_widget)
        content_layout.addWidget(self.pages)
        content_layout.addWidget(self.right_sidebar)

        central_layout.addLayout(content_layout)

        central_widget = QWidget()
        central_widget.setLayout(central_layout)
        self.setCentralWidget(central_widget)

        # Данные для чатов (простая логика)
        self.chats_data = {
            "🟢 Alex": [
                (False, "Привет! Как дела?"),
                (True, "Привет, всё отлично! Ты как?"),
                (False, "Тоже хорошо, спасибо!"),
            ],
            "🟡 Jordan": [
                (False, "Ты сегодня будешь на стриме?"),
                (True, "Да, в 8 вечера."),
            ],
            "🔴 Maria": [
                (False, "Отправила тебе фото."),
            ],
            "🟢 Chris": [],
            "🔴 Taylor": [],
        }

        self.current_chat = None

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

    def uncheck_others(self):
        sender = self.sender()
        for btn in self.sidebar_buttons + [self.settings_button]:
            if btn != sender:
                btn.setChecked(False)

        if sender == self.settings_button:
            self.switch_page(5)
        else:
            idx = self.sidebar_buttons.index(sender)
            self.switch_page(idx)

    def switch_page(self, index):
        self.pages.setCurrentIndex(index)
        # Правая панель видна только на страницах "Chats" и "Servers"
        self.right_sidebar.setVisible(index in [1, 2])
        for i, btn in enumerate(self.sidebar_buttons):
            btn.setChecked(i == index)
        self.settings_button.setChecked(index == 5)

    def create_top_bar(self):
        bar = QWidget()
        bar.setFixedHeight(60)
        bar.setStyleSheet("background-color: #111118;")
        layout = QHBoxLayout()
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(10)

        logo = QLabel()
        pix = QPixmap("icons/logo.png")
        if not pix.isNull():
            logo.setPixmap(pix.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))

        title = QLabel("DUMP")
        title.setStyleSheet("color: #d8ff56; font-size: 28px; font-weight: 900;")

        layout.addWidget(logo)
        layout.addWidget(title)
        layout.addStretch()

        bar.setLayout(layout)
        return bar

    def create_profile_page(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title = QLabel("User Profile")
        title.setStyleSheet("font-size: 28px; color: #d8ff56; font-weight: 900;")

        avatar = QLabel()
        pix = QPixmap("icons/avatar.png")
        if not pix.isNull():
            avatar.setPixmap(pix.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        avatar.setStyleSheet("border-radius: 60px;")

        bio = QTextEdit("About me...")
        bio.setStyleSheet("""
            background-color: #2c2c3c;
            color: white;
            border-radius: 12px;
            padding: 12px;
            font-size: 16px;
        """)
        bio.setFixedHeight(150)

        layout.addWidget(title, alignment=Qt.AlignLeft)
        layout.addWidget(avatar, alignment=Qt.AlignLeft)
        layout.addWidget(bio)
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
                font-size: 14px;
                border-right: 1px solid #2e2e40;
            }
            QListWidget::item {
                color: #eeeeee;
                padding: 12px 10px;
                margin: 4px;
                border-radius: 8px;
            }
            QListWidget::item:selected {
                background-color: #d8ff56;
                color: #000000;
                font-weight: bold;
            }
        """)
        # Добавляем пользователей с их статусами (как в скриншоте)
        users = ["🟢 Alex", "🟡 Jordan", "🔴 Maria", "🟢 Chris", "🔴 Taylor"]
        for user in users:
            self.contact_list.addItem(QListWidgetItem(user))
        self.contact_list.currentItemChanged.connect(self.load_chat)

        # --- Chat area
        chat_area = QVBoxLayout()
        chat_area.setContentsMargins(10, 10, 10, 10)
        chat_area.setSpacing(10)

        # Заголовок с ником и кнопками звонков
        self.chat_header_widget = QWidget()
        self.chat_header_widget.setFixedHeight(50)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)

        self.chat_header = QLabel("Select a user to start chatting")
        self.chat_header.setStyleSheet("font-size: 20px; font-weight: 900; color: #d8ff56;")
        header_layout.addWidget(self.chat_header)

        header_layout.addStretch()

        # Кнопки аудио и видео звонков (иконки из папки icons)
        self.audio_call_btn = QPushButton()
        self.audio_call_btn.setIcon(QIcon("icons/call.png"))
        self.audio_call_btn.setIconSize(QSize(28, 28))
        self.audio_call_btn.setFixedSize(36, 36)
        self.audio_call_btn.setStyleSheet("background: transparent; border: none;")
        self.audio_call_btn.setToolTip("Audio Call")
        self.audio_call_btn.setCursor(Qt.PointingHandCursor)
        self.audio_call_btn.hide()  # Скрываем по умолчанию
        header_layout.addWidget(self.audio_call_btn)

        self.video_call_btn = QPushButton()
        self.video_call_btn.setIcon(QIcon("icons/video_call.png"))
        self.video_call_btn.setIconSize(QSize(28, 28))
        self.video_call_btn.setFixedSize(36, 36)
        self.video_call_btn.setStyleSheet("background: transparent; border: none;")
        self.video_call_btn.setToolTip("Video Call")
        self.video_call_btn.setCursor(Qt.PointingHandCursor)
        self.video_call_btn.hide()  # Скрываем по умолчанию
        header_layout.addWidget(self.video_call_btn)

        self.chat_header_widget.setLayout(header_layout)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            background-color: #2c2c3c;
            color: white;
            border-radius: 12px;
            padding: 12px;
            font-size: 14px;
        """)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #444444;")

        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Type a message...")
        self.chat_input.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e2f;
                color: white;
                padding: 12px;
                border-radius: 12px;
                border: 1px solid #444;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #d8ff56;
            }
        """)
        self.chat_input.setDisabled(True)
        self.chat_input.returnPressed.connect(self.send_message)

        emoji_btn = QPushButton()
        emoji_btn.setIcon(QIcon("icons/emoji.png"))
        emoji_btn.setToolTip("Insert emoji")
        emoji_btn.setStyleSheet("background: transparent; border: none;")
        emoji_btn.setCursor(Qt.PointingHandCursor)

        photo_btn = QPushButton()
        photo_btn.setIcon(QIcon("icons/photo.png"))
        photo_btn.setToolTip("Attach photo")
        photo_btn.setStyleSheet("background: transparent; border: none;")
        photo_btn.setCursor(Qt.PointingHandCursor)

        send_button = QPushButton("Send")
        send_button.setStyleSheet("""
            QPushButton {
                background-color: #d8ff56;
                color: black;
                padding: 10px 20px;
                border-radius: 12px;
                font-weight: 900;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #ecff87;
            }
        """)
        send_button.clicked.connect(self.send_message)

        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)
        input_layout.addWidget(self.chat_input)
        input_layout.addWidget(emoji_btn)
        input_layout.addWidget(photo_btn)
        input_layout.addWidget(send_button)

        chat_area.addWidget(self.chat_header_widget)
        chat_area.addWidget(self.chat_display)
        chat_area.addWidget(line)
        chat_area.addLayout(input_layout)

        layout.addWidget(self.contact_list)
        layout.addLayout(chat_area)
        widget.setLayout(layout)

        return widget

    def load_chat(self):
        selected = self.contact_list.currentItem()
        if selected:
            username = selected.text()
            self.chat_header.setText(username)
            self.chat_display.clear()
            # Показываем кнопки звонков при выборе чата
            self.audio_call_btn.show()
            self.video_call_btn.show()
            # Загружаем историю сообщений из self.chats_data
            messages = self.chats_data.get(username, [])
            for sender, msg in messages:
                if sender:
                    # Мои сообщения с префиксом You: и зелёным фоном
                    self.chat_display.append(
                        f"<p style='color:black; background:#d8ff56; padding:6px; border-radius:8px; max-width:70%; float:right; clear:both;'>"
                        f"<b>You:</b> {msg}</p>")
                else:
                    # Ник и сообщение собеседника
                    self.chat_display.append(
                        f"<p style='color:#d8ff56; font-weight: 700; margin-bottom: 2px; max-width:70%; float:left; clear:both;'>{username}</p>")
                    self.chat_display.append(
                        f"<p style='color:#eeeeee; background:#3a3a4a; padding:6px; border-radius:8px; max-width:70%; float:left; clear:both; margin-top:0;'>{msg}</p>")
            self.chat_display.moveCursor(QTextCursor.End)
            self.chat_input.setDisabled(False)
            self.chat_input.setFocus()
            self.current_chat = username
        else:
            # Нет выбранного чата — скрываем кнопки звонков
            self.chat_header.setText("Select a user to start chatting")
            self.chat_display.clear()
            self.chat_input.setDisabled(True)
            self.audio_call_btn.hide()
            self.video_call_btn.hide()
            self.current_chat = None

    def send_message(self):
        text = self.chat_input.text().strip()
        if text and hasattr(self, "current_chat") and self.current_chat:
            # Добавляем сообщение в чат
            self.chats_data.setdefault(self.current_chat, []).append((True, text))
            # Отображаем в окне чата с префиксом You:
            self.chat_display.append(
                f"<p style='color:black; background:#d8ff56; padding:6px; border-radius:8px; max-width:70%; float:right; clear:both;'>"
                f"<b>You:</b> {text}</p>")
            self.chat_display.moveCursor(QTextCursor.End)
            self.chat_input.clear()

    def create_saved_page(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Заголовок "Saved Messages" без иконок звонков
        header_widget = QWidget()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)

        title = QLabel("Saved Messages")
        title.setStyleSheet("font-size: 24px; font-weight: 900; color: #d8ff56;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        header_widget.setLayout(header_layout)

        # Окно сообщений
        self.saved_chat_display = QTextEdit()
        self.saved_chat_display.setReadOnly(True)
        self.saved_chat_display.setStyleSheet("""
            background-color: #2c2c3c;
            color: white;
            border-radius: 12px;
            padding: 12px;
            font-size: 14px;
        """)

        # Линия разделитель
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #444444;")

        # Поле ввода и кнопки эмодзи, фото и отправки рядом снизу (без видео)
        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)

        self.saved_chat_input = QLineEdit()
        self.saved_chat_input.setPlaceholderText("Type a message...")
        self.saved_chat_input.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e2f;
                color: white;
                padding: 12px;
                border-radius: 12px;
                border: 1px solid #444;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #d8ff56;
            }
        """)
        self.saved_chat_input.returnPressed.connect(self.send_saved_message)

        self.saved_emoji_btn = QPushButton()
        self.saved_emoji_btn.setIcon(QIcon("icons/emoji.png"))
        self.saved_emoji_btn.setIconSize(QSize(28, 28))
        self.saved_emoji_btn.setFixedSize(36, 36)
        self.saved_emoji_btn.setStyleSheet("background: transparent; border: none;")
        self.saved_emoji_btn.setToolTip("Insert emoji")
        self.saved_emoji_btn.setCursor(Qt.PointingHandCursor)

        self.saved_photo_btn = QPushButton()
        self.saved_photo_btn.setIcon(QIcon("icons/photo.png"))
        self.saved_photo_btn.setIconSize(QSize(28, 28))
        self.saved_photo_btn.setFixedSize(36, 36)
        self.saved_photo_btn.setStyleSheet("background: transparent; border: none;")
        self.saved_photo_btn.setToolTip("Attach photo")
        self.saved_photo_btn.setCursor(Qt.PointingHandCursor)

        send_button = QPushButton("Send")
        send_button.setStyleSheet("""
            QPushButton {
                background-color: #d8ff56;
                color: black;
                padding: 10px 20px;
                border-radius: 12px;
                font-weight: 900;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #ecff87;
            }
        """)
        send_button.clicked.connect(self.send_saved_message)

        input_layout.addWidget(self.saved_chat_input)
        input_layout.addWidget(self.saved_emoji_btn)
        input_layout.addWidget(self.saved_photo_btn)
        input_layout.addWidget(send_button)

        layout.addWidget(header_widget)
        layout.addWidget(self.saved_chat_display)
        layout.addWidget(line)
        layout.addLayout(input_layout)

        widget.setLayout(layout)

        # Загрузим сохранённые сообщения в окно
        self.load_saved_messages()

        return widget

    def load_saved_messages(self):
        self.saved_chat_display.clear()
        for sender, msg in self.saved_messages:
            # Все сообщения белым цветом на тёмном фоне, без выделения "You:"
            self.saved_chat_display.append(
                f"<p style='color:#eeeeee; background:#3a3a4a; padding:6px; border-radius:8px; max-width:70%; float:right; clear:both;'>{msg}</p>")
        self.saved_chat_display.moveCursor(QTextCursor.End)

    def send_saved_message(self):
        text = self.saved_chat_input.text().strip()
        if text:
            self.saved_messages.append((True, text))
            self.saved_chat_display.append(
                f"<p style='color:#eeeeee; background:#3a3a4a; padding:6px; border-radius:8px; max-width:70%; float:right; clear:both;'>{text}</p>")
            self.saved_chat_display.moveCursor(QTextCursor.End)
            self.saved_chat_input.clear()

    def create_servers_page(self):
        return self.basic_page("Servers", "Server list will be here...")

    def create_friends_page(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title = QLabel("Friends")
        title.setStyleSheet("font-size: 28px; color: #d8ff56; font-weight: 900;")
        layout.addWidget(title, alignment=Qt.AlignLeft)

        # Статистика друзей
        self.friends_data = [
            {"name": "Alex", "status": "Playing Valorant", "online": True},
            {"name": "Jordan", "status": "Online", "online": True},
            {"name": "Chris", "status": "Offline", "online": False},
            {"name": "Maria", "status": "In Game", "online": True},
            {"name": "Taylor", "status": "Offline", "online": False},
            {"name": "Sam", "status": "Idle", "online": True},
        ]

        total = len(self.friends_data)
        online_count = sum(1 for f in self.friends_data if f["online"])
        offline_count = total - online_count

        stats_label = QLabel(
            f"Friends: {total} | Online: {online_count} | Offline: {offline_count}"
        )
        stats_label.setStyleSheet("font-size: 16px; color: #d6e9a8; margin-bottom: 10px;")
        layout.addWidget(stats_label, alignment=Qt.AlignLeft)

        # Поиск
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Find friends...")
        self.search_input.setStyleSheet("""
            background-color: #2c2c3c;
            padding: 10px;
            color: white;
            border-radius: 12px;
            font-size: 14px;
        """)
        layout.addWidget(self.search_input)

        # Список друзей
        self.friends_list_widget = QListWidget()
        self.friends_list_widget.setStyleSheet("""
            QListWidget {
                background-color: #1a1a26;
                border-radius: 12px;
                padding: 10px;
                font-size: 16px;
                color: #d6e9a8;
            }
            QListWidget::item {
                padding: 8px 10px;
                border-radius: 8px;
            }
            QListWidget::item:hover {
                background-color: #2c2c3c;
            }
        """)
        layout.addWidget(self.friends_list_widget)

        self.populate_friends_list(self.friends_data)

        self.search_input.textChanged.connect(self.filter_friends)

        widget.setLayout(layout)
        return widget

    def populate_friends_list(self, friends):
        self.friends_list_widget.clear()
        for friend in friends:
            status_icon = "🟢" if friend["online"] else "🔴"
            item_text = f"{status_icon} {friend['name']} — {friend['status']}"
            item = QListWidgetItem(item_text)
            self.friends_list_widget.addItem(item)

    def filter_friends(self, text):
        text = text.lower()
        filtered = [
            f for f in self.friends_data
            if text in f["name"].lower() or text in f["status"].lower()
        ]
        self.populate_friends_list(filtered)

    def create_settings_page(self):
        return self.basic_page("Settings", "Settings section is under development...")

    def basic_page(self, title_text, content, editable=False):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title = QLabel(title_text)
        title.setStyleSheet("font-size: 28px; color: #d8ff56; font-weight: 900;")

        if editable:
            content_widget = QTextEdit(content)
        else:
            content_widget = QLabel(content)

        content_widget.setStyleSheet("""
            background-color: #2c2c3c;
            color: white;
            border-radius: 12px;
            padding: 12px;
            font-size: 14px;
        """)

        layout.addWidget(title, alignment=Qt.AlignLeft)
        layout.addWidget(content_widget)
        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def create_right_sidebar(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        widget.setStyleSheet("background-color: #13131a;")

        title = QLabel("Friends Online")
        title.setStyleSheet("font-size: 20px; color: #d8ff56; font-weight: 900;")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setSpacing(10)

        friends = [("Alex", "In Game"), ("Jordan", "Idle"), ("Maria", "Online")]
        for name, status in friends:
            label = QLabel(f"🟢 {name} — {status}")
            label.setStyleSheet("font-size: 16px; color: #d6e9a8; padding: 6px;")
            container_layout.addWidget(label)

        container_layout.addStretch()
        container.setLayout(container_layout)
        scroll.setWidget(container)

        layout.addWidget(scroll)
        widget.setLayout(layout)
        return widget


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatApp()
    window.show()
    sys.exit(app.exec_())

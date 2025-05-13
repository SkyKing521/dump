"""
UI Mockup для DUMP

Основные компоненты:
- AuthWindow: Окно аутентификации (логин/регистрация)
- StartWindow: Стартовое окно после входа
- ChatWindow: Окно списка чатов
- Chat: Окно конкретного чата
- FriendsWindow: Окно списка друзей
- ServerWindow: Окно серверов
- SavedMessagesWindow: Окно сохраненных сообщений
- ProfileWindow: Окно профиля пользователя
- SettingsWindow: Окно настроек
Для бэкенд-разработчиков:
Все (ну почти) обработчики событий (кнопок, полей ввода) помечены как TODO
"""

import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QFrame, QLineEdit, QScrollArea, 
    QSpacerItem, QSizePolicy, QListWidget, QListWidgetItem, 
    QTabWidget, QStackedWidget, QCheckBox
)
from PyQt5.QtGui import QPixmap, QIcon, QFont, QFontDatabase, QColor, QPainter
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, pyqtProperty, QEasingCurve, QRect, QPoint
from PyQt5.QtWidgets import QGraphicsDropShadowEffect

# --- Константы стилей ---
PRIMARY_COLOR = "#f8a5c2"
HOVER_COLOR = "#ffc0cb"
BG_COLOR = "#2f2f3a"
SIDEBAR_COLOR = "#1e1e28"
TEXT_COLOR = "#f8a5c2"

# --- Вспомогательные функции ---
def apply_shadow(widget):
    """Применяет тень к виджету"""
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(12)
    shadow.setColor(QColor(HOVER_COLOR))
    shadow.setOffset(0, 0)
    widget.setGraphicsEffect(shadow)

def style_button(button, bg=PRIMARY_COLOR, hover=HOVER_COLOR, size=40, icon_size=20):
    """Стилизует кнопку с иконкой"""
    button.setFixedSize(size, size)
    button.setIconSize(QSize(icon_size, icon_size))
    button.setStyleSheet(f"""
        QPushButton {{
            background-color: {bg};
            border-radius: {size//2}px;
            border: none;
        }}
        QPushButton:hover {{
            background-color: {hover};
        }}
    """)

def style_nav_button(button, font=None):
    """Стилизует навигационную кнопку"""
    if font:
        button.setFont(font)
    button.setStyleSheet(f"""
        QPushButton {{
            color: {PRIMARY_COLOR};
            text-align: left;
            background: none;
            border: none;
            padding: 6px;
        }}
        QPushButton:hover {{
            color: {HOVER_COLOR};
            background-color: rgba(255,255,255,0.05);
            border-radius: 8px;
        }}
    """)

def create_icon_button(path, size=36, icon_size=20):
    """Создает кнопку с иконкой"""
    btn = QPushButton()
    btn.setIcon(QIcon(path))
    style_button(btn, size=size, icon_size=icon_size)
    return btn

class BaseWindow(QWidget):
    """Базовое окно с общими для всех окон элементами"""
    def __init__(self, title, use_right_sidebar=True):
        super().__init__()
        self.setWindowTitle(title)
        self.setStyleSheet(f"background-color: {BG_COLOR}; color: {TEXT_COLOR};")
        self.setMinimumSize(1000, 600)
        self.use_right_sidebar = use_right_sidebar

        self.load_fonts()
        self.setLayout(QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.setup_ui()

    def load_fonts(self):
        """Загружает кастомные шрифты"""
        font_id = QFontDatabase.addApplicationFont("RibeyeMarrow.ttf")
        family = QFontDatabase.applicationFontFamilies(font_id)[0]
        self.ribeye = QFont(family, 12)
        self.default_font = QFont("Segoe UI", 10)

    def setup_ui(self):
        """Настраивает базовый UI (левая/правая панели)"""
        self.layout().addWidget(self.create_left_sidebar())
        self.center_frame = QFrame()
        self.center_frame.setStyleSheet(f"background-color: {BG_COLOR};")
        self.center_layout = QVBoxLayout(self.center_frame)
        self.center_layout.setContentsMargins(0, 0, 0, 0)
        self.center_layout.setSpacing(0)
        self.layout().addWidget(self.center_frame)
        
        if self.use_right_sidebar:
            self.layout().addWidget(self.create_right_sidebar())

    def create_left_sidebar(self):
        """Создает левую навигационную панель"""
        sidebar = QFrame()
        sidebar.setFixedWidth(190)
        sidebar.setStyleSheet(f"background-color: {SIDEBAR_COLOR};")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 12, 12, 12)

        # Логотип и название
        logo_layout = QHBoxLayout()
        logo = QLabel()
        logo.setPixmap(QPixmap("icons/logo.png").scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo_layout.addWidget(logo)
        name = QLabel("DUMP")
        name.setFont(self.ribeye)
        logo_layout.addWidget(name)
        logo_layout.addStretch()
        layout.addLayout(logo_layout)

        # Навигационные кнопки
        nav_buttons = [
            ("My profile", "avatar.png"), 
            ("Chats", "chat.png"),
            ("Servers", "server.png"), 
            ("Friends", "friends.png"),
            ("Saved messages", "saved.png")
        ]
        
        for text, icon in nav_buttons:
            btn = QPushButton(text)
            btn.setIcon(QIcon(f"icons/{icon}"))
            btn.setIconSize(QSize(24, 24))
            style_nav_button(btn, font=self.default_font)
            layout.addWidget(btn)

        layout.addStretch()

        # Кнопка настроек
        settings = QPushButton("Settings")
        settings.setIcon(QIcon("icons/settings.png"))
        settings.setIconSize(QSize(24, 24))
        style_nav_button(settings, font=self.default_font)
        layout.addWidget(settings)

        return sidebar

    def create_right_sidebar(self):
        """Создает правую информационную панель"""
        sidebar = QFrame()
        sidebar.setFixedWidth(190)
        sidebar.setStyleSheet(f"background-color: {SIDEBAR_COLOR};")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 12, 12, 12)

        header = QHBoxLayout()
        label = QLabel("Friends in game")
        label.setFont(self.default_font)
        header.addWidget(label)
        header.addStretch()
        header.addWidget(create_icon_button("icons/question.png", size=24, icon_size=16))
        layout.addLayout(header)

        info = QLabel("Don't have any friends yet...")
        info.setStyleSheet("color: rgba(248,165,194,0.5);")
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)
        layout.addStretch()

        return sidebar

class ToggleButton(QCheckBox):
    """Кастомный переключатель (toggle)"""
    def __init__(self, width=50):
        super().__init__()
        self.setFixedSize(width, 28)
        self.setCursor(Qt.PointingHandCursor)

        self._bg_color = "#444"
        self._circle_color = "#fff"
        self._active_color = PRIMARY_COLOR
        self._circle_position = 2

        self.animation = QPropertyAnimation(self, b"circle_position")
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.setDuration(180)
        self.stateChanged.connect(self.start_transition)

    @pyqtProperty(int)
    def circle_position(self):
        return self._circle_position

    @circle_position.setter
    def circle_position(self, pos):
        self._circle_position = pos
        self.update()

    def start_transition(self, value):
        """Анимация переключения"""
        self.animation.setStartValue(self.circle_position)
        self.animation.setEndValue(self.width() - 26 if value else 2)
        self.animation.start()

    def hitButton(self, pos: QPoint):
        return self.contentsRect().contains(pos)

    def paintEvent(self, e):
        """Отрисовка toggle-кнопки"""
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        p.setPen(Qt.NoPen)

        # Фон
        p.setBrush(QColor(self._active_color if self.isChecked() else self._bg_color))
        p.drawRoundedRect(rect, rect.height() / 2, rect.height() / 2)

        # Круглый переключатель
        p.setBrush(QColor(self._circle_color))
        p.drawEllipse(self._circle_position, 2, 24, 24)

class StartWindow(BaseWindow):
    """Стартовое окно после входа"""
    def __init__(self):
        super().__init__("DUMP")

    def setup_ui(self):
        super().setup_ui()
        btn = QPushButton("Start using bro :)")
        btn.setFont(self.default_font)
        btn.setFixedSize(200, 50)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {PRIMARY_COLOR};
                color: #1f1e27;
                font-weight: bold;
                border-radius: 25px;
            }}
            QPushButton:hover {{
                background-color: {HOVER_COLOR};
            }}
        """)
        # TODO: Добавить обработчик нажатия
        self.center_layout.addStretch()
        self.center_layout.addWidget(btn, alignment=Qt.AlignCenter)
        self.center_layout.addStretch()

class ChatWindow(BaseWindow):
    """Окно списка чатов"""
    def __init__(self):
        super().__init__("DUMP Chat")

    def setup_ui(self):
        super().setup_ui()

        # Поле поиска
        search = QLineEdit()
        search.setPlaceholderText("Search...")
        search.setStyleSheet("""
            QLineEdit {background: white; color: #2f2f3a; padding: 6px; border-radius: 6px; margin-top: 12px;}
        """)
        self.center_layout.addWidget(search)

        # Список чатов
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: transparent; border: none;")

        container = QWidget()
        self.chat_list = QVBoxLayout(container)
        self.scroll.setWidget(container)

        # TODO: Заменить на реальные данные из API
        self.chat_list.addWidget(self.create_chat_entry("какая-то вумен", "текст сообщения", "icons/avatar.png", "5"))
        self.chat_list.addStretch()
        self.center_layout.addWidget(self.scroll)

        # Кнопка добавления чата
        self.plus_btn = create_icon_button("icons/plus.png", size=48, icon_size=24)
        self.plus_btn.setParent(self.center_frame)
        # TODO: Добавить обработчик нажатия

    def resizeEvent(self, event):
        """Позиционирование кнопки добавления чата"""
        super().resizeEvent(event)
        if hasattr(self, 'plus_btn'):
            self.plus_btn.move(self.center_frame.width() - 68, self.center_frame.height() - 68)

    def create_chat_entry(self, username, message, avatar_path, badge=None):
        """Создает элемент списка чатов"""
        btn = QPushButton(f"{username}\n{message}")
        btn.setIcon(QIcon(avatar_path))
        btn.setIconSize(QSize(32, 32))
        btn.setFont(QFont("Segoe UI", 9))
        btn.setStyleSheet(f"""
            QPushButton {{
                color: {PRIMARY_COLOR};
                text-align: left;
                background: none;
                border: none;
                padding: 8px;
            }}
            QPushButton:hover {{
                background: rgba(255,255,255,0.05);
                border-radius: 8px;
            }}
        """)
        # TODO: Добавить обработчик нажатия

        if badge:
            lbl = QLabel(badge, btn)
            lbl.setFixedSize(20, 20)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"""
                QLabel {{
                    background: {PRIMARY_COLOR};
                    color: #1f1e27;
                    border-radius: 10px;
                    font-weight: bold;
                }}
            """)
            btn.resizeEvent = lambda e: lbl.move(btn.width() - 30, 10)

        return btn

class Chat(BaseWindow):
    """Окно конкретного чата"""
    def __init__(self):
        super().__init__("DUMP Chat", use_right_sidebar=False)

    def setup_ui(self):
        self.layout().addWidget(self.create_icon_sidebar())
        self.layout().addWidget(self.create_chat_list_sidebar())
        self.center_frame = QFrame()
        self.center_frame.setStyleSheet(f"background-color: {BG_COLOR};")
        self.center_layout = QVBoxLayout(self.center_frame)
        self.center_layout.setContentsMargins(0, 0, 0, 0)
        self.center_layout.setSpacing(0)
        self.layout().addWidget(self.center_frame)
        self.setup_chat()
    def create_icon_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(60)
        sidebar.setStyleSheet(f"background-color: {SIDEBAR_COLOR};")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(6, 6, 6, 6)
        icons = ["avatar.png", "chat.png", "server.png", "friends.png", "saved.png"]
        for icon_name in icons:
            btn = QPushButton()
            btn.setIcon(QIcon(f"icons/{icon_name}"))
            btn.setIconSize(QSize(24, 24))
            style_button(btn, size=40, icon_size=20)
            layout.addWidget(btn)
        layout.addStretch()
        settings_btn = QPushButton()
        settings_btn.setIcon(QIcon("icons/settings.png"))
        settings_btn.setIconSize(QSize(24, 24))
        style_button(settings_btn, size=40, icon_size=20)
        layout.addWidget(settings_btn)
        return sidebar
    def create_chat_list_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(230)
        sidebar.setStyleSheet(f"background-color: #1e1e2c;")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        title = QLabel("Chats")
        title.setFont(self.default_font)
        title.setStyleSheet(f"color: {TEXT_COLOR}; font-weight: bold;")
        layout.addWidget(title)

        search_input = QLineEdit()
        search_input.setPlaceholderText("Search...")
        search_input.setFont(self.default_font)
        search_input.setStyleSheet("""
            QLineEdit {
             background-color: #2a293a;
             color: white;
             padding: 6px 10px;
             border-radius: 8px;
             font-size: 12px;
             border: none;
         }
         """)
        layout.addWidget(search_input)

        # TODO: Здесь можно вставить динамическую подгрузку чатов с API
        for name in ["Helena Hills", "John Doe", "Server Admin"]:
            chat_btn = QPushButton(name)
            chat_btn.setFont(self.default_font)
            chat_btn.setStyleSheet(f"""QPushButton {{ color: {TEXT_COLOR}; text-align: left; background-color: transparent; padding: 6px; border: none; border-radius: 6px;}} QPushButton:hover {{ background-color: rgba(255, 255, 255, 0.05);}}""")
            layout.addWidget(chat_btn)
        layout.addStretch()
        return sidebar

    def setup_chat(self):
        # Шапка чата
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet(f"background-color: {PRIMARY_COLOR};")
        hlayout = QHBoxLayout(header)
        hlayout.setContentsMargins(20, 0, 20, 0)

        avatar = QLabel()
        avatar.setPixmap(QPixmap("icons/avatar.png").scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        name = QLabel("Helena Hills")
        name.setFont(self.default_font)
        name.setStyleSheet("color: black; font-weight: bold;")
        status = QLabel("Active 20m ago")
        status.setFont(self.default_font)
        status.setStyleSheet("color: black; font-size: 10px;")

        name_status = QVBoxLayout()
        name_status.addWidget(name)
        name_status.addWidget(status)

        hlayout.addWidget(avatar)
        hlayout.addLayout(name_status)
        hlayout.addStretch()
        hlayout.addWidget(create_icon_button("icons/call.png"))
        hlayout.addWidget(create_icon_button("icons/video.png"))
        self.center_layout.addWidget(header)

        # Область сообщений
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(f"background-color: {BG_COLOR}; border: none;")
        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.scroll.setWidget(self.messages_widget)
        self.center_layout.addWidget(self.scroll)

        # TODO: Загрузить сообщения из API
        # self.add_message("Сегодня", "center")
        # self.add_message("Привет!", "left")
        # self.add_message("Как дела?", "right")

        # Поле ввода сообщения
        input_frame = QFrame()
        input_frame.setFixedHeight(60)
        input_frame.setStyleSheet(f"background-color: {SIDEBAR_COLOR}; border-top: 1px solid #3a394a;")
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(10, 0, 10, 0)

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Enter your message...")
        self.message_input.setFont(self.default_font)
        self.message_input.setStyleSheet("""
            QLineEdit {
                background-color: #2a293a;
                color: white;
                padding: 10px;
                border-radius: 8px;
                font-size: 12px;
                border: none;
            }
        """)
        # TODO: Добавить обработчик отправки сообщения
        input_layout.addWidget(self.message_input)

        for icon in ["mic_on", "clip.png", "emoji.png", "send.png"]:
            btn = create_icon_button(f"icons/{icon}")
            # TODO: Добавить обработчики нажатий
            input_layout.addWidget(btn)

        self.center_layout.addWidget(input_frame)

    def add_message(self, text, side):
        """Добавляет сообщение в чат"""
        if side == "center":
            label = QLabel(text)
            label.setFont(self.default_font)
            label.setStyleSheet("color: rgba(248,165,194,0.6); font-size: 10px;")
            label.setAlignment(Qt.AlignCenter)
            self.messages_layout.insertWidget(self.messages_layout.count() - 1, label)
        else:
            bubble = QFrame()
            layout = QHBoxLayout(bubble)
            msg = QLabel(text)
            msg.setFont(self.default_font)
            msg.setWordWrap(True)
            msg.setStyleSheet(f"""
                background-color: {PRIMARY_COLOR if side == "right" else "#e6e6e6"};
                color: black;
                padding: 8px 12px;
                border-radius: 12px;
            """)
            layout.addStretch() if side == "right" else None
            layout.addWidget(msg)
            layout.addStretch() if side == "left" else None
            self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble)

class ServerWindow(BaseWindow):
    """Окно серверов"""
    def __init__(self):
        super().__init__("DUMP Servers")

    def setup_ui(self):
        main_layout = self.layout()
        main_layout.addWidget(self.create_left_sidebar())
        main_layout.addWidget(self.create_main_content())
        main_layout.addWidget(self.create_right_sidebar())

    def create_main_content(self):
        """Создает основное содержимое окна серверов"""
        wrapper = QFrame()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Поле поиска
        search = QLineEdit()
        search.setPlaceholderText("Search servers...")
        search.setStyleSheet("""
            QLineEdit {
                background: white;
                color: #2f2f3a;
                padding: 6px;
                border-radius: 6px;
                margin-top: 10px;
            }
        """)
        layout.addWidget(search)

        # Кнопка создания сервера
        new_server_btn = QPushButton()
        new_server_btn.setFont(self.default_font)
        new_server_btn.setFixedHeight(40)
        new_server_btn.setIcon(QIcon("icons/plus.png"))
        new_server_btn.setIconSize(QSize(18, 18))
        new_server_btn.setText("  New Server")
        new_server_btn.setStyleSheet("""
            QPushButton { 
                background-color: #f8a5c2; 
                color: #1f1e27; 
                border-radius: 20px; 
                padding: 0 20px; 
                font-weight: bold; 
                text-align: center;
            }
            QPushButton:hover { 
                background-color: #ffc0cb;
            } 
        """)
        # TODO: Добавить обработчик нажатия
        layout.addWidget(new_server_btn, alignment=Qt.AlignLeft)

        # Список серверов
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")

        cnt = QWidget()
        v_layout = QVBoxLayout(cnt)

        # TODO: Заменить на реальные данные из API
        v_layout.addWidget(self.create_server_button("Best Server", "some description...", "icons/server.png"))
        v_layout.addStretch()
        scroll.setWidget(cnt)
        layout.addWidget(scroll)

        return wrapper

    def create_server_button(self, name, description, icon_path):
        """Создает кнопку сервера"""
        btn = QPushButton()
        btn.setFont(QFont("Segoe UI", 9))
        btn.setIcon(QIcon(icon_path))
        btn.setIconSize(QSize(32, 32))
        btn.setStyleSheet("""
            QPushButton {
                color: #f8a5c2;
                text-align: left;
                background: none;
                border: none;
                padding: 8px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 8px;
            }
        """)
        btn.setText(f"{name}\n{description}")
        # TODO: Добавить обработчик нажатия
        return btn

class FriendsWindow(BaseWindow):
    """Окно списка друзей"""
    def __init__(self):
        super().__init__("Friends", use_right_sidebar=False)

    def setup_ui(self):
        self.layout().addWidget(self.create_left_sidebar())
        self.layout().addWidget(self.create_separator())

        self.center_frame = QFrame()
        self.center_frame.setStyleSheet(f"background-color: {SIDEBAR_COLOR};")
        self.center_layout = QVBoxLayout(self.center_frame)
        self.center_layout.setContentsMargins(20, 20, 20, 20)
        self.center_layout.setSpacing(20)
        self.layout().addWidget(self.center_frame)

        # Заголовок
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        friends_label = QLabel("Friends")
        friends_label.setFont(QFont(self.default_font.family(), 28, QFont.Bold))
        friends_label.setStyleSheet(f"color: {PRIMARY_COLOR};")

        question_button = create_icon_button("icons/question.png", size=32, icon_size=18)
        question_button.setCursor(Qt.ArrowCursor)
        question_button.setFixedSize(36, 36)
        question_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {PRIMARY_COLOR};
                border-radius: 18px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {HOVER_COLOR};
            }}
        """)
        # TODO: Добавить обработчик нажатия

        header_layout.addWidget(friends_label)
        header_layout.addStretch()
        header_layout.addWidget(question_button)

        self.center_layout.addLayout(header_layout)

        # Поле поиска
        search_input = QLineEdit()
        search_input.setPlaceholderText("Search...")
        search_input.setFont(self.default_font)
        search_input.setStyleSheet(f"""
            background-color: #ffffff;
            color: {BG_COLOR};
            border: none;
            border-radius: 8px;
            padding: 8px 12px;
        """)
        search_input.setFixedWidth(300)
        self.center_layout.addWidget(search_input)

        # Список онлайн-друзей
        online_frame = QFrame()
        online_layout = QVBoxLayout(online_frame)
        online_layout.setContentsMargins(0, 0, 0, 0)
        online_label = QLabel("Online")
        online_label.setFont(QFont(self.default_font.family(), 14, QFont.Bold))
        online_label.setStyleSheet(f"color: {PRIMARY_COLOR};")
        online_layout.addWidget(online_label)

        self.online_list = QListWidget()
        self.online_list.setSelectionMode(QListWidget.NoSelection)
        self.online_list.setFocusPolicy(Qt.NoFocus)
        self.online_list.setStyleSheet(f"""
            background: {SIDEBAR_COLOR};
            border: none;
            border-radius: 8px;
            padding: 8px;
        """)
        online_layout.addWidget(self.online_list)
        self.center_layout.addWidget(online_frame)

        self.center_layout.addStretch()

        # Список оффлайн-друзей
        offline_frame = QFrame()
        offline_layout = QVBoxLayout(offline_frame)
        offline_layout.setContentsMargins(0, 0, 0, 0)

        offline_label = QLabel("Offline")
        offline_label.setFont(QFont(self.default_font.family(), 14, QFont.Bold))
        offline_label.setStyleSheet(f"color: {PRIMARY_COLOR};")
        offline_layout.addWidget(offline_label)

        self.offline_list = QListWidget()
        self.offline_list.setSelectionMode(QListWidget.NoSelection)
        self.offline_list.setFocusPolicy(Qt.NoFocus)
        self.offline_list.setStyleSheet(f"""
            background: {SIDEBAR_COLOR};
            border: none;
            border-radius: 8px;
            padding: 8px;
        """)
        offline_layout.addWidget(self.offline_list)
        self.center_layout.addWidget(offline_frame)

        self.center_layout.addStretch()
        self.populate_friends()

    def populate_friends(self):
        """Заполняет списки друзей"""
        # TODO: Заменить на реальные данные из API
        online_friends = []
        offline_friends = []

        if online_friends:
            for friend in online_friends:
                self.online_list.addItem(friend)
        else:
            self.add_placeholder(self.online_list, "No friends online")

        if offline_friends:
            for friend in offline_friends:
                self.offline_list.addItem(friend)
        else:
            self.add_placeholder(self.offline_list, "No friends offline")

    def add_placeholder(self, list_widget, text):
        """Добавляет заглушку в пустой список"""
        placeholder = QListWidgetItem(text)
        placeholder.setFlags(Qt.NoItemFlags)
        placeholder.setForeground(QColor(200, 200, 200, 128))
        placeholder.setFont(QFont(self.default_font.family(), 11))
        list_widget.addItem(placeholder)

    def create_separator(self):
        """Создает разделитель между панелями"""
        separator = QFrame()
        separator.setFixedWidth(1) 
        separator.setStyleSheet("background-color: rgba(255, 255, 255, 0.2);")  
        return separator

class SavedMessagesWindow(BaseWindow):
    """Окно сохраненных сообщений"""
    def __init__(self):
        super().__init__("Saved Messages", use_right_sidebar=False)

    def setup_ui(self):
        super().setup_ui()
        self.setup_chat()

    def setup_chat(self):
        # Шапка
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet(f"background-color: {PRIMARY_COLOR};")
        hlayout = QHBoxLayout(header)
        hlayout.setContentsMargins(20, 0, 20, 0)

        saved_label = QLabel("Saved Messages")
        saved_label.setFont(self.default_font)
        saved_label.setStyleSheet("color: black; font-weight: bold; font-size: 14px;")

        hlayout.addWidget(saved_label)
        hlayout.addStretch()

        # Поле поиска
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.search_input.setFont(self.default_font)
        self.search_input.setFixedHeight(30)
        self.search_input.setFixedWidth(200)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: white;
                color: black;
                padding: 5px 10px;
                border-radius: 8px;
                font-size: 12px;
                border: none;
            }
        """)
        # TODO: Добавить обработчик поиска
        hlayout.addWidget(self.search_input)
        self.center_layout.addWidget(header)

        # Область сообщений
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(f"background-color: {BG_COLOR}; border: none;")

        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.scroll.setWidget(self.messages_widget)
        self.center_layout.addWidget(self.scroll)

        # TODO: Загрузить сохраненные сообщения из API

        # Поле ввода сообщения
        input_frame = QFrame()
        input_frame.setFixedHeight(60)
        input_frame.setStyleSheet(f"background-color: {SIDEBAR_COLOR}; border-top: 1px solid #3a394a;")
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(10, 0, 10, 0)

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Enter your message...")
        self.message_input.setFont(self.default_font)
        self.message_input.setStyleSheet("""
            QLineEdit {
                background-color: #2a293a;
                color: white;
                padding: 10px;
                border-radius: 8px;
                font-size: 12px;
                border: none;
            }
        """)
        # TODO: Добавить обработчик отправки сообщения
        input_layout.addWidget(self.message_input)

        for icon in ["mic_on.png", "clip.png", "emoji.png", "send.png"]:
            btn = create_icon_button(f"icons/{icon}")
            # TODO: Добавить обработчики нажатий
            input_layout.addWidget(btn)

        self.center_layout.addWidget(input_frame)

    def add_message(self, text, side):
        """Добавляет сообщение в сохраненные"""
        if side == "center":
            label = QLabel(text)
            label.setFont(self.default_font)
            label.setStyleSheet("color: rgba(248,165,194,0.6); font-size: 10px;")
            label.setAlignment(Qt.AlignCenter)
            self.messages_layout.insertWidget(self.messages_layout.count() - 1, label)
        else:
            bubble = QFrame()
            layout = QHBoxLayout(bubble)
            layout.setContentsMargins(10, 5, 10, 5)

            msg = QLabel(text)
            msg.setFont(self.default_font)
            msg.setWordWrap(True)
            msg.setStyleSheet(f"""
                background-color: {PRIMARY_COLOR if side == "right" else "#e6e6e6"};
                color: black;
                padding: 8px 12px;
                border-radius: 12px;
            """)
            if side == "right":
                layout.addStretch()
                layout.addWidget(msg)
            else:
                layout.addWidget(msg)
                layout.addStretch()

            self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble)

class AuthWindow(QWidget):
    """Окно аутентификации (логин/регистрация)"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Authentication")
        self.setFixedSize(600, 800)
        self.setStyleSheet(f"background-color: {BG_COLOR};")
        self.load_fonts()
        self.setup_ui()

    def load_fonts(self):
        """Загружает кастомные шрифты"""
        font_id = QFontDatabase.addApplicationFont("RibeyeMarrow.ttf")
        family = QFontDatabase.applicationFontFamilies(font_id)[0]
        self.ribeye = QFont(family, 14)
        self.default_font = QFont("Segoe UI", 10)

    def setup_ui(self):
        """Настраивает UI окна аутентификации"""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # Шапка
        self.header = QFrame()
        self.header.setFixedHeight(80)
        self.header.setStyleSheet(f"background-color: {PRIMARY_COLOR};")
        
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        
        self.logo = QLabel()
        self.logo.setPixmap(QPixmap("icons/logo.png").scaled(40, 40))
        
        self.title = QLabel("DUMP")
        self.title.setFont(self.ribeye)
        self.title.setStyleSheet("color: black;")
        
        header_layout.addWidget(self.logo)
        header_layout.addWidget(self.title)
        header_layout.addStretch()
        
        self.help_btn = QPushButton("?")
        self.help_btn.setFixedSize(30, 30)
        self.help_btn.setStyleSheet("""
            QPushButton {
                background: white;
                border-radius: 15px;
                color: black;
                font-weight: bold;
            }
        """)
        # TODO: Добавить обработчик нажатия
        header_layout.addWidget(self.help_btn)
        
        self.layout.addWidget(self.header)

        # Основное содержимое (страницы логина/регистрации)
        self.main_content = QStackedWidget()
        self.main_content.setStyleSheet("""
            background-color: #2f2f3a;
            border: none;
        """)
        
        # Страница логина
        self.login_page = self.create_login_page()
        self.main_content.addWidget(self.login_page)
        
        # Страница регистрации
        self.signup_page = self.create_signup_page()
        self.main_content.addWidget(self.signup_page)
        
        self.layout.addWidget(self.main_content)

    def create_login_page(self):
        """Создает страницу входа"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Заголовок
        title = QLabel("Welcome back!")
        title.setStyleSheet("""
            color: white;
            font-size: 18px;
            font-weight: bold;
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Поле email
        self.login_email = QLineEdit()
        self.login_email.setPlaceholderText("Email")
        self.login_email.setStyleSheet("""
            QLineEdit {
                background: white;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                border: none;
            }
        """)
        layout.addWidget(self.login_email)
        
        # Поле пароля с переключателем видимости
        password_frame = QFrame()
        password_layout = QHBoxLayout(password_frame)
        password_layout.setContentsMargins(0, 0, 0, 0)
        
        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("Password")
        self.login_password.setEchoMode(QLineEdit.Password)
        self.login_password.setStyleSheet("""
            QLineEdit {
                background: white;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                border: none;
            }
        """)
        
        self.login_eye_btn = QPushButton()
        self.login_eye_btn.setIcon(QIcon("icons/eye_closed.png"))
        self.login_eye_btn.setFixedSize(24, 24)
        self.login_eye_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                padding: 0;
            }
        """)
        self.login_eye_btn.clicked.connect(self.toggle_login_password)
        
        password_layout.addWidget(self.login_password)
        password_layout.addWidget(self.login_eye_btn)
        layout.addWidget(password_frame)
        
        # Кнопка входа
        login_btn = QPushButton("Login")
        login_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {PRIMARY_COLOR};
                color: black;
                border-radius: 8px;
                padding: 12px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {HOVER_COLOR};
            }}
        """)
        login_btn.clicked.connect(self.handle_login)
        layout.addWidget(login_btn)
        
        # Ссылка на регистрацию
        switch_text = QLabel("Don't have an account? <a href='#'>Sign up</a>")
        switch_text.setStyleSheet("color: white;")
        switch_text.setAlignment(Qt.AlignCenter)
        switch_text.setOpenExternalLinks(False)
        switch_text.linkActivated.connect(lambda: self.main_content.setCurrentIndex(1))
        layout.addWidget(switch_text)
        
        layout.addStretch()
        return page

    def create_signup_page(self):
        """Создает страницу регистрации"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Заголовок
        title = QLabel("Create an account")
        title.setStyleSheet("""
            color: white;
            font-size: 18px;
            font-weight: bold;
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Поле email
        self.signup_email = QLineEdit()
        self.signup_email.setPlaceholderText("Email")
        self.signup_email.setStyleSheet("""
            QLineEdit {
                background: white;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                border: none;
            }
        """)
        layout.addWidget(self.signup_email)
        
        # Поле имени пользователя
        self.signup_username = QLineEdit()
        self.signup_username.setPlaceholderText("Username")
        self.signup_username.setStyleSheet("""
            QLineEdit {
                background: white;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                border: none;
            }
        """)
        layout.addWidget(self.signup_username)
        
        # Поле пароля с переключателем видимости
        password_frame = QFrame()
        password_layout = QHBoxLayout(password_frame)
        password_layout.setContentsMargins(0, 0, 0, 0)
        
        self.signup_password = QLineEdit()
        self.signup_password.setPlaceholderText("Password")
        self.signup_password.setEchoMode(QLineEdit.Password)
        self.signup_password.setStyleSheet("""
            QLineEdit {
                background: white;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                border: none;
            }
        """)
        
        self.signup_eye_btn = QPushButton()
        self.signup_eye_btn.setIcon(QIcon("icons/eye_closed.png"))
        self.signup_eye_btn.setFixedSize(24, 24)
        self.signup_eye_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                padding: 0;
            }
        """)
        self.signup_eye_btn.clicked.connect(self.toggle_signup_password)
        
        password_layout.addWidget(self.signup_password)
        password_layout.addWidget(self.signup_eye_btn)
        layout.addWidget(password_frame)
        
        # Поле подтверждения пароля
        confirm_frame = QFrame()
        confirm_layout = QHBoxLayout(confirm_frame)
        confirm_layout.setContentsMargins(0, 0, 0, 0)
        
        self.signup_confirm = QLineEdit()
        self.signup_confirm.setPlaceholderText("Confirm Password")
        self.signup_confirm.setEchoMode(QLineEdit.Password)
        self.signup_confirm.setStyleSheet("""
            QLineEdit {
                background: white;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                border: none;
            }
        """)
        
        self.confirm_eye_btn = QPushButton()
        self.confirm_eye_btn.setIcon(QIcon("icons/eye_closed.png"))
        self.confirm_eye_btn.setFixedSize(24, 24)
        self.confirm_eye_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                padding: 0;
            }
        """)
        self.confirm_eye_btn.clicked.connect(self.toggle_confirm_password)
        
        confirm_layout.addWidget(self.signup_confirm)
        confirm_layout.addWidget(self.confirm_eye_btn)
        layout.addWidget(confirm_frame)
        
        # Кнопка регистрации
        signup_btn = QPushButton("Sign Up")
        signup_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {PRIMARY_COLOR};
                color: black;
                border-radius: 8px;
                padding: 12px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {HOVER_COLOR};
            }}
        """)
        signup_btn.clicked.connect(self.handle_signup)
        layout.addWidget(signup_btn)
        
        # Ссылки на условия
        terms = QLabel('By signing up, you agree to our <a href="#">Terms</a> and <a href="#">Privacy Policy</a>')
        terms.setStyleSheet("color: white; font-size: 11px;")
        terms.setAlignment(Qt.AlignCenter)
        terms.setOpenExternalLinks(True)
        layout.addWidget(terms)
        
        # Ссылка на вход
        switch_text = QLabel("Already have an account? <a href='#'>Log in</a>")
        switch_text.setStyleSheet("color: white;")
        switch_text.setAlignment(Qt.AlignCenter)
        switch_text.setOpenExternalLinks(False)
        switch_text.linkActivated.connect(lambda: self.main_content.setCurrentIndex(0))
        layout.addWidget(switch_text)
        
        layout.addStretch()
        return page

    def toggle_login_password(self):
        """Переключает видимость пароля на странице входа"""
        if self.login_password.echoMode() == QLineEdit.Password:
            self.login_password.setEchoMode(QLineEdit.Normal)
            self.login_eye_btn.setIcon(QIcon("icons/eye_open.png"))
        else:
            self.login_password.setEchoMode(QLineEdit.Password)
            self.login_eye_btn.setIcon(QIcon("icons/eye_closed.png"))

    def toggle_signup_password(self):
        """Переключает видимость пароля на странице регистрации"""
        if self.signup_password.echoMode() == QLineEdit.Password:
            self.signup_password.setEchoMode(QLineEdit.Normal)
            self.signup_eye_btn.setIcon(QIcon("icons/eye_open.png"))
        else:
            self.signup_password.setEchoMode(QLineEdit.Password)
            self.signup_eye_btn.setIcon(QIcon("icons/eye_closed.png"))

    def toggle_confirm_password(self):
        """Переключает видимость подтверждения пароля"""
        if self.signup_confirm.echoMode() == QLineEdit.Password:
            self.signup_confirm.setEchoMode(QLineEdit.Normal)
            self.confirm_eye_btn.setIcon(QIcon("icons/eye_open.png"))
        else:
            self.signup_confirm.setEchoMode(QLineEdit.Password)
            self.confirm_eye_btn.setIcon(QIcon("icons/eye_closed.png"))

    def handle_login(self):
        """Обработчик входа"""
        # TODO: Интегрировать с API
        email = self.login_email.text()
        password = self.login_password.text()
        print(f"Login attempt with email: {email}")

    def handle_signup(self):
        """Обработчик регистрации"""
        # TODO: Интегрировать с API
        email = self.signup_email.text()
        username = self.signup_username.text()
        password = self.signup_password.text()
        confirm = self.signup_confirm.text()
        print(f"Signup attempt with username: {username}, email: {email}")

class ProfileWindow(BaseWindow):
    """Окно профиля пользователя"""
    def __init__(self):
        super().__init__("Profile", use_right_sidebar=True)
        self.setup_profile_ui()

    def setup_profile_ui(self):
        """Настраивает UI профиля"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # Аватар и основная информация
        top_layout = QHBoxLayout()
        top_layout.setSpacing(20)

        self.avatar_label = QLabel()
        pixmap = QPixmap("icons/avatar.png").scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.avatar_label.setPixmap(pixmap)
        self.avatar_label.setFixedSize(100, 100)
        self.avatar_label.setStyleSheet("border-radius: 50px;")
        top_layout.addWidget(self.avatar_label)

        user_info_layout = QVBoxLayout()
        user_info_layout.setSpacing(5)

        self.username_label = QLabel("Helena")
        self.username_label.setFont(QFont(self.ribeye.family(), 22))
        self.username_label.setStyleSheet(f"color: {PRIMARY_COLOR};")

        self.status_label = QLabel("Active 20 minutes ago")
        self.status_label.setFont(self.default_font)
        self.status_label.setStyleSheet("color: rgba(248,165,194,0.5);")

        self.about_label = QLabel("Тут короче какая-то офигеть\nглубокомысленная цитата")
        self.about_label.setFont(self.default_font)
        self.about_label.setStyleSheet("color: white;")
        self.about_label.setWordWrap(True)

        user_info_layout.addWidget(self.username_label)
        user_info_layout.addWidget(self.status_label)
        user_info_layout.addWidget(self.about_label)
        top_layout.addLayout(user_info_layout)
        main_layout.addLayout(top_layout)

        # Действия
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(12)

        self.search_chat_btn = self.create_action_button("Search chat", "icons/search.png")
        self.sent_images_btn = self.create_action_button("Sent images", "icons/photo.png")
        self.sent_videos_btn = self.create_action_button("Sent videos", "icons/video.png")
        self.sent_files_btn = self.create_action_button("Sent files", "icons/file.png")
        self.shared_links_btn = self.create_action_button("Shared links", "icons/link.png")

        for btn in [
            self.search_chat_btn, self.sent_images_btn, self.sent_videos_btn,
            self.sent_files_btn, self.shared_links_btn
        ]:
            actions_layout.addWidget(btn)

        actions_wrapper = QFrame()
        actions_wrapper.setLayout(actions_layout)
        actions_wrapper.setMaximumWidth(300)
        main_layout.addWidget(actions_wrapper)

        # Переключатель уведомлений
        notifications_layout = QHBoxLayout()
        notifications_layout.setSpacing(10)
        notifications_layout.setContentsMargins(0, 20, 0, 0)

        notifications_label = QLabel("Notifications")
        notifications_label.setFont(self.default_font)
        notifications_label.setFixedWidth(100)

        self.notifications_checkbox = ToggleButton(width=50)
        self.notifications_checkbox.setChecked(True)
        # TODO: Добавить обработчик изменения состояния

        notifications_layout.addWidget(notifications_label)
        notifications_layout.addWidget(self.notifications_checkbox)
        notifications_layout.addStretch()
        main_layout.addLayout(notifications_layout)

        main_layout.addStretch()
        self.center_layout.addLayout(main_layout)

    def create_action_button(self, text, icon_path):
        """Создает кнопку действия в профиле"""
        btn = QPushButton(text)
        btn.setIcon(QIcon(icon_path))
        btn.setIconSize(QSize(20, 20))
        style_nav_button(btn, font=self.default_font)
        btn.setMaximumWidth(280)
        # TODO: Добавить обработчик нажатия
        return btn

class SettingsWindow(BaseWindow):
    """Окно настроек"""
    def __init__(self):
        super().__init__("Settings", use_right_sidebar=False)
        self.setup_settings_ui()

    def setup_settings_ui(self):
        """Настраивает UI окна настроек"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        container = QWidget()
        scroll.setWidget(container)

        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(30)

        # Навигация
        nav_layout = QHBoxLayout()
        nav_buttons = ["Profile", "Voice and video", "Chats", "Hot keys", "Language", "More"]
        for name in nav_buttons:
            btn = QPushButton(name)
            btn.setFont(self.default_font)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #2B2B3B;
                    color: {TEXT_COLOR};
                    border: none;
                    padding: 8px 16px;
                    border-radius: 8px;
                }}
                QPushButton:hover {{
                    background-color: rgba(255,255,255,0.05);
                }}
            """)
            # TODO: Добавить обработчик нажатия
            nav_layout.addWidget(btn)
        main_layout.addLayout(nav_layout)

        # Основное содержимое
        content_layout = QHBoxLayout()
        content_layout.setSpacing(40)
        content_layout.setStretch(0, 1)
        content_layout.setStretch(1, 1)

        # Левый блок
        form_layout = QVBoxLayout()
        form_layout.setSpacing(20)

        top_info = QHBoxLayout()
        avatar = QLabel()
        avatar.setPixmap(QPixmap("icons/avatar.png").scaled(96, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        avatar.setFixedSize(96, 96)
        top_info.addWidget(avatar)

        name_label = QLabel("UGANDA CHILD")
        name_label.setFont(QFont("Segoe UI", 14))
        top_info.addWidget(name_label)
        top_info.addStretch()
        form_layout.addLayout(top_info)

        for label in ["Username", "Real name", "About me"]:
            form_layout.addLayout(self.labeled_input(label))

        form_layout.addWidget(self.make_label("Location"))
        for field in ["Country", "Region", "City"]:
            form_layout.addWidget(self.make_input(field))

        content_layout.addLayout(form_layout)

        # Правый блок
        illus_layout = QVBoxLayout()
        illus_layout.setSpacing(10)
        illus_layout.addWidget(self.make_label("Illustration"))
        illus_layout.addWidget(self.make_input("Add illustration link"))

        image = QLabel()
        image.setPixmap(QPixmap("icons/illustration_placeholder.jpg").scaled(260, 260, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        image.setFixedSize(260, 260)
        image.setAlignment(Qt.AlignCenter)
        illus_layout.addWidget(image)
        illus_layout.addStretch()

        content_layout.addLayout(illus_layout)
        main_layout.addLayout(content_layout)

        self.center_layout.addWidget(scroll)

    def make_label(self, text):
        """Создает стилизованную метку"""
        label = QLabel(text)
        label.setStyleSheet(f"color: {PRIMARY_COLOR};")
        label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        return label

    def make_input(self, placeholder):
        """Создает стилизованное поле ввода"""
        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder)
        input_field.setStyleSheet(f"""
            background-color: #4B4B4B;
            color: {PRIMARY_COLOR};
            border: none;
            padding: 6px;
            border-radius: 6px;
        """)
        input_field.setFont(QFont("Segoe UI", 9))
        return input_field

    def labeled_input(self, label_text):
        """Создает пару метка-поле ввода"""
        layout = QVBoxLayout()
        layout.addWidget(self.make_label(label_text))
        layout.addWidget(self.make_input(""))
        return layout

# --- Точка входа ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Для тестирования разных окон раскомментируйте нужное:
    window = Chat()   
    #window = ChatWindow() 
    #window = StartWindow()
    #window = ServerWindow()
    #window = FriendsWindow()
    #window = SavedMessagesWindow()
    #window = AuthWindow() 
    #window = ProfileWindow()
    #window = SettingsWindow()
    window.show()
    sys.exit(app.exec_())

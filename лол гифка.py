import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QFileDialog
from PyQt5.QtGui import QPixmap, QMovie
from PyQt5.QtCore import Qt

class ImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        # Настройка главного окна
        self.setWindowTitle("Просмотр изображений и GIF")
        self.setGeometry(100, 100, 400, 400)

        # Создание метки для отображения изображения/GIF
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(self.image_label)

        # Автоматическое открытие диалога выбора файла
        self.open_file_dialog()

    def open_file_dialog(self):
        # Открываем диалог выбора файла
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите изображение или GIF",
            "",
            "Images (*.png *.jpg *.jpeg *.gif);;All Files (*)",
            options=options
        )

        if file_path:
            self.load_media(file_path)
        else:
            self.close()  # Закрываем приложение, если файл не выбран

    def load_media(self, file_path):
        if file_path.lower().endswith('.gif'):
            # Загрузка анимированного GIF
            self.movie = QMovie(file_path)
            self.image_label.setMovie(self.movie)
            self.movie.start()
        else:
            # Загрузка статического изображения
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                self.image_label.setPixmap(pixmap.scaled(
                    400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation
                ))
            else:
                print("Ошибка загрузки изображения.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = ImageViewer()
    viewer.show()
    sys.exit(app.exec_())

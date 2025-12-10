import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QLabel, QPushButton, QHBoxLayout, QFrame)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QFont, QColor, QPainter, QBrush


class MacOSNotification(QFrame):
    """Уведомление в стиле macOS"""
    
    def __init__(self, message="Добро пожаловать!", parent=None):
        super().__init__(parent)
        self.message = message
        self.setup_ui()
        
    def setup_ui(self):
        """Настройка интерфейса уведомления"""
        # Прозрачный фон для рисования тени
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Основной контейнер
        self.container = QFrame(self)
        self.container.setObjectName("notificationContainer")
        self.container.setStyleSheet("""
            #notificationContainer {
                background-color: rgba(40, 40, 40, 230);
                border-radius: 10px;
                border: 1px solid rgba(100, 100, 100, 150);
                padding: 20px 15px 15px 15px;  /* Больше отступ сверху для крестика */
            }
        """)
        
        # Макет контейнера
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # Кнопка закрытия (черный крестик в левом верхнем углу)
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(16, 16)
        
        # Располагаем крестик абсолютно позиционированным в левом верхнем углу
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #ffffff;
                font-weight: bold;
                font-size: 14px;
                border: none;
                padding: 0;
                margin: 0;
            }
            QPushButton:hover {
                color: #cccccc;
            }
            QPushButton:pressed {
                color: #aaaaaa;
            }
        """)
        self.close_btn.clicked.connect(self.close_notification)
        
        # Сообщение
        self.message_label = QLabel(self.message)
        self.message_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: normal;
                padding: 0;
                margin: 0;
            }
        """)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Добавляем в контейнер
        container_layout.addWidget(self.message_label)
        
        # Основной layout для позиционирования крестика
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.container)
        
        # Позиционируем крестик поверх контейнера в левом верхнем углу
        self.close_btn.setParent(self)
        
        # Анимация
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(400)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
    def resizeEvent(self, event):
        """Обработчик изменения размера - позиционируем крестик"""
        super().resizeEvent(event)
        
        # Позиционируем крестик в левом верхнем углу прямоугольника
        # Смещаем на 5px внутрь от края
        self.close_btn.move(5, 5)
        
    def show_notification(self, x, y):
        """Показать уведомление с анимацией"""
        # Устанавливаем фиксированный размер (300x72 - на 40% меньше 120)
        self.setFixedSize(300, 72)
        
        # Начальная позиция (за экраном сверху)
        self.move(x, -self.height())
        
        # Конечная позиция
        end_pos = self.pos()
        end_pos.setY(y)
        
        self.animation.setStartValue(self.pos())
        self.animation.setEndValue(end_pos)
        
        self.show()
        self.animation.start()
        
        # Позиционируем крестик после показа
        self.close_btn.move(5, 5)
        self.close_btn.raise_()  # Поднимаем на передний план
        
    def close_notification(self):
        """Закрыть уведомление с анимацией"""
        self.animation.setStartValue(self.pos())
        self.animation.setEndValue(self.pos().x(), -self.height())
        self.animation.finished.connect(self.hide)
        self.animation.start()
        
    def paintEvent(self, event):
        """Рисование тени для уведомления"""
        # Создаем эффект тени
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Рисуем тень
        shadow_color = QColor(0, 0, 0, 40)
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Внешняя тень
        for i in range(1, 6):
            painter.setBrush(QBrush(shadow_color))
            painter.drawRoundedRect(i, i, 
                                   self.container.width() + 2, 
                                   self.container.height() + 2, 
                                   10, 10)
            shadow_color.setAlpha(shadow_color.alpha() - 8)
            
        painter.end()
        super().paintEvent(event)


class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self):
        super().__init__()
        # Инициализируем notification как None ДО setup_ui
        self.notification = None
        self.setup_ui()
        
    def setup_ui(self):
        """Настройка интерфейса главного окна"""
        # Устанавливаем окно на весь экран
        self.setWindowTitle("Демо уведомлений macOS")
        self.showFullScreen()
        
        # Центральный виджет
        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: #1a1a1a;")
        self.setCentralWidget(central_widget)
        
        # Макет с информацией
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Информационная метка
        info_label = QLabel("Демонстрация уведомления в стиле macOS")
        info_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
                padding: 20px;
            }
        """)
        
        # Описание особенностей
        features = QLabel("Особенности этого уведомления:\n"
                         "• Темный прямоугольник с закругленными краями\n"
                         "• Светлый текст внутри\n"
                         "• Высота уменьшена на 40%\n"
                         "• Черный крестик без фона в левом верхнем углу\n"
                         "• Закрывается только крестиком")
        features.setStyleSheet("color: #aaa; font-size: 14px; padding: 20px;")
        features.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Кнопка для показа уведомления
        self.show_notification_btn = QPushButton("Показать уведомление снова")
        self.show_notification_btn.setFixedSize(250, 50)
        self.show_notification_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d5aa0;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3d6ab0;
            }
            QPushButton:pressed {
                background-color: #1d4a90;
            }
        """)
        self.show_notification_btn.clicked.connect(self.show_welcome_notification)
        
        # Инструкция по закрытию
        instruction = QLabel("Попробуйте закрыть уведомление черным крестиком в левом верхнем углу")
        instruction.setStyleSheet("color: #ffcc00; font-size: 16px; padding: 20px; font-weight: bold;")
        instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(info_label)
        layout.addWidget(features)
        layout.addWidget(self.show_notification_btn, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(instruction)
        
        # Показываем приветственное уведомление через 1 секунду
        QTimer.singleShot(1000, self.show_welcome_notification)
        
    def show_welcome_notification(self):
        """Показать приветственное уведомление"""
        # Удаляем старое уведомление, если есть
        if self.notification:
            self.notification.deleteLater()
            
        # Создаем новое уведомление
        self.notification = MacOSNotification("Добро пожаловать!", self)
        
        # Позиционируем в правом верхнем углу
        screen_width = self.width()
        notification_x = screen_width - 320  # 300 ширина + 20 отступ
        notification_y = 20  # Отступ сверху
        
        # Показываем с анимацией
        self.notification.show_notification(notification_x, notification_y)
        
    def resizeEvent(self, event):
        """Обработчик изменения размера окна"""
        super().resizeEvent(event)
        
        # При изменении размера окна перепозиционируем уведомление
        # Проверяем, что notification существует И видимо
        if hasattr(self, 'notification') and self.notification and self.notification.isVisible():
            screen_width = self.width()
            notification_x = screen_width - 320
            self.notification.move(notification_x, 20)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
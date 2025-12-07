from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QApplication, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QRect, pyqtSignal, QObject, QDate, QDateTime
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtSql import QSqlQueryModel
from database.db_manager import DatabaseManager
from datetime import datetime, timedelta


class NotificationSignals(QObject):
    """Signals для уведомлений"""
    notification_triggered = pyqtSignal(dict)  # {'type': 'warning', 'title': '', 'message': ''}


class NotificationWidget(QWidget):
    """Mac-style всплывающее уведомление"""
    
    def __init__(self, parent=None, notification_type='info', title='', message=''):
        super().__init__(parent)
        self.notification_type = notification_type
        self.auto_close_time = 4000  # ms
        self.animation_duration = 300  # ms
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setup_ui(title, message)
        self.setup_animation()
        self.setup_colors()
        
    def setup_ui(self, title, message):
        """Настройка интерфейса уведомления"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        
        # Заголовок
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(11)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Сообщение
        message_label = QLabel(message)
        message_font = QFont()
        message_font.setPointSize(10)
        message_label.setFont(message_font)
        message_label.setWordWrap(True)
        layout.addWidget(message_label)
        
        # Тень (Mac-style)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(shadow)
        
        self.setMinimumWidth(320)
        self.setMaximumWidth(380)
        
    def setup_colors(self):
        """Установка цветов в зависимости от типа"""
        colors = {
            'info': {'bg': '#F5F5F7', 'text': '#333333'},
            'warning': {'bg': '#FFF3CD', 'text': '#856404'},
            'error': {'bg': '#F8D7DA', 'text': '#721C24'},
            'success': {'bg': '#D4EDDA', 'text': '#155724'},
        }
        
        color_set = colors.get(self.notification_type, colors['info'])
        
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {color_set['bg']};
                border-radius: 8px;
                border: 1px solid {self.get_border_color(self.notification_type)};
            }}
            QLabel {{
                color: {color_set['text']};
            }}
        """)
        
    def get_border_color(self, notif_type):
        """Получение цвета границы"""
        borders = {
            'info': '#E0E0E2',
            'warning': '#FFC107',
            'error': '#DC3545',
            'success': '#28A745',
        }
        return borders.get(notif_type, '#E0E0E2')
        
    def setup_animation(self):
        """Настройка анимации появления/исчезновения"""
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(self.animation_duration)
        
        # Таймер для автозакрытия
        self.close_timer = QTimer()
        self.close_timer.setSingleShot(True)
        self.close_timer.timeout.connect(self.fade_out)
        
    def show_notification(self):
        """Показать уведомление с анимацией"""
        # Позиция в верхнем правом углу
        screen = QApplication.primaryScreen()
        screen_rect = screen.availableGeometry()
        
        # Стартовая позиция (за экраном сверху)
        start_y = screen_rect.top() - self.height() - 10
        end_y = screen_rect.top() + 20
        
        # Финальная позиция
        end_x = screen_rect.right() - self.width() - 20
        
        start_rect = QRect(end_x, start_y, self.width(), self.height())
        end_rect = QRect(end_x, end_y, self.width(), self.height())
        
        self.animation.setStartValue(start_rect)
        self.animation.setEndValue(end_rect)
        
        self.show()
        self.animation.start()
        
        # Запуск таймера на автозакрытие
        self.close_timer.start(self.auto_close_time)
        
    def fade_out(self):
        """Исчезновение уведомления"""
        screen = QApplication.primaryScreen()
        screen_rect = screen.availableGeometry()
        
        current_geometry = self.geometry()
        end_y = screen_rect.top() - self.height() - 10
        
        end_rect = QRect(current_geometry.x(), end_y, self.width(), self.height())
        
        self.animation.setStartValue(current_geometry)
        self.animation.setEndValue(end_rect)
        self.animation.finished.connect(self.close)
        
        self.animation.start()


class NotificationManager:
    """Менеджер уведомлений и проверки сроков"""
    
    def __init__(self, main_window=None):
        self.db = DatabaseManager()
        self.main_window = main_window
        self.signals = NotificationSignals()
        self.check_timer = QTimer()
        self.check_timer.setSingleShot(False)
        self.check_timer.timeout.connect(self._check_deadlines)
        self.notification_widgets = []
        
    def start_checking(self, interval_ms=60000):
        """Запустить периодическую проверку сроков (по умолчанию каждую минуту)"""
        print("🔔 Запуск проверки сроков уведомлений...")
        self.check_timer.start(interval_ms)
        # Сразу проверяем при старте
        self._check_deadlines()
        
    def stop_checking(self):
        """Остановить проверку сроков"""
        self.check_timer.stop()
        
    def _check_deadlines(self):
        """Проверка сроков возврата и создание уведомлений"""
        try:
            today = QDate.currentDate()
            tomorrow = today.addDays(1)
            
            # Получаем активы, которые нужно вернуть
            query = """
                SELECT 
                    uh.history_id,
                    a.asset_id,
                    a.name,
                    e.last_name || ' ' || e.first_name as employee_name,
                    uh.planned_return_date,
                    uh.actual_return_date,
                    DATE('now') as today
                FROM Usage_History uh
                JOIN Assets a ON uh.asset_id = a.asset_id
                JOIN Employees e ON uh.employee_id = e.employee_id
                WHERE uh.operation_type = 'выдача'
                    AND uh.actual_return_date IS NULL
                    AND DATE(uh.planned_return_date) <= DATE('+1 day')
                ORDER BY uh.planned_return_date ASC
            """
            
            results = self.db.execute_query(query)
            
            for row in results:
                history_id, asset_id, asset_name, employee_name, planned_date_str, _, _ = row
                
                planned_date = QDate.fromString(planned_date_str, "yyyy-MM-dd")
                
                # Определяем тип уведомления
                if planned_date == today:
                    notif_type = 'error'
                    title = '⚠️ Срок истекает сегодня'
                    message = f'{asset_name}\nу {employee_name}'
                elif planned_date == tomorrow:
                    notif_type = 'warning'
                    title = '⏰ Завтра истекает срок'
                    message = f'{asset_name}\nу {employee_name}'
                elif planned_date < today:
                    notif_type = 'error'
                    title = '🚨 Инструмент просрочен'
                    message = f'{asset_name}\nу {employee_name}'
                    # Обновляем примечание в истории
                    self._mark_as_overdue(history_id)
                else:
                    continue
                
                # Показываем уведомление
                self.show_notification(notif_type, title, message)
                
        except Exception as e:
            print(f"❌ Ошибка при проверке сроков: {e}")
    
    def _mark_as_overdue(self, history_id):
        """Отметить запись как просроченную"""
        try:
            # Проверяем, уже ли отмечена как просроченная
            result = self.db.execute_query(
                "SELECT notes FROM Usage_History WHERE history_id = ?",
                (history_id,)
            )
            
            if result:
                notes = result[0][0] or ""
                if "Просрочено" not in notes:
                    new_notes = f"{notes}\n[Просрочено: {QDate.currentDate().toString('yyyy-MM-dd')}]" if notes else f"[Просрочено: {QDate.currentDate().toString('yyyy-MM-dd')}]"
                    self.db.execute_update(
                        "UPDATE Usage_History SET notes = ? WHERE history_id = ?",
                        (new_notes, history_id)
                    )
        except Exception as e:
            print(f"❌ Ошибка при отметке как просроченная: {e}")
    
    def show_notification(self, notif_type='info', title='', message=''):
        """Показать всплывающее уведомление"""
        try:
            notification = NotificationWidget(
                self.main_window,
                notification_type=notif_type,
                title=title,
                message=message
            )
            
            notification.show_notification()
            self.notification_widgets.append(notification)
            
            # Удаляем из списка после закрытия
            def on_close():
                if notification in self.notification_widgets:
                    self.notification_widgets.remove(notification)
            
            notification.destroyed.connect(on_close)
            
            print(f"📬 Уведомление: {title} - {message}")
            
        except Exception as e:
            print(f"❌ Ошибка при показе уведомления: {e}")
    
    def get_overdue_assets(self):
        """Получить список просроченных активов"""
        try:
            query = """
                SELECT 
                    a.asset_id,
                    a.name,
                    e.last_name || ' ' || e.first_name as employee_name,
                    uh.planned_return_date,
                    CAST((DATE('now') - DATE(uh.planned_return_date)) AS INTEGER) as days_overdue
                FROM Usage_History uh
                JOIN Assets a ON uh.asset_id = a.asset_id
                JOIN Employees e ON uh.employee_id = e.employee_id
                WHERE uh.operation_type = 'выдача'
                    AND uh.actual_return_date IS NULL
                    AND DATE(uh.planned_return_date) < DATE('now')
                ORDER BY uh.planned_return_date ASC
            """
            
            return self.db.execute_query(query)
            
        except Exception as e:
            print(f"❌ Ошибка при получении просроченных активов: {e}")
            return []
    
    def cleanup(self):
        """Очистка при закрытии приложения"""
        self.stop_checking()
        for widget in self.notification_widgets:
            try:
                widget.close()
            except:
                pass

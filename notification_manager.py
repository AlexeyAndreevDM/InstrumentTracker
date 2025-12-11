from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QApplication, QGraphicsDropShadowEffect, QPushButton)
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
    
    def __init__(self, parent=None, notification_type='info', title='', message='', persistent=False, variant='default'):
        super().__init__(parent)
        self.notification_type = notification_type
        self.auto_close_time = 4000  # ms
        self.animation_duration = 300  # ms
        self.persistent = persistent
        self.variant = variant
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setup_ui(title, message)
        self.setup_animation()
        
    def setup_ui(self, title, message):
        """Настройка интерфейса уведомления"""
        from PyQt6.QtWidgets import QFrame
        
        # Основной layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Контейнер для уведомления
        self.container = QFrame(self)
        self.container.setObjectName("notificationContainer")
        
        # Выбираем стиль в зависимости от variant
        if self.variant == 'dark':
            bg_color = "rgba(40, 40, 40, 230)"
            text_color = "#ffffff"
            border_color = "rgba(100, 100, 100, 150)"
        else:
            # Для других типов - белый фон
            bg_color = "rgba(255, 255, 255, 240)"
            text_color = "#000000"
            border_color = "rgba(200, 200, 200, 150)"
        
        self.container.setStyleSheet(f"""
            #notificationContainer {{
                background-color: {bg_color};
                border-radius: 10px;
                border: 1px solid {border_color};
                padding: 15px 15px 15px 15px;
            }}
        """)
        
        # Макет контейнера
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(8)
        
        # Заголовок
        if title:
            title_label = QLabel(title)
            title_font = QFont()
            title_font.setBold(True)
            title_font.setPointSize(12)
            title_label.setFont(title_font)
            title_label.setStyleSheet(f"color: {text_color}; margin: 0; padding: 0;")
            container_layout.addWidget(title_label)
        
        # Сообщение
        if message:
            message_label = QLabel(message)
            message_font = QFont()
            message_font.setPointSize(11)
            message_label.setFont(message_font)
            message_label.setWordWrap(True)
            message_label.setStyleSheet(f"color: {text_color}; margin: 0; padding: 0;")
            container_layout.addWidget(message_label)
        
        main_layout.addWidget(self.container)
        
        # Кнопка закрытия (для persistent)
        if self.persistent:
            self.close_btn = QPushButton("✕")
            self.close_btn.setFixedSize(16, 16)
            self.close_btn.setParent(self)
            self.close_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {text_color};
                    font-weight: bold;
                    font-size: 14px;
                    border: none;
                    padding: 0;
                    margin: 0;
                }}
                QPushButton:hover {{
                    color: #cccccc;
                }}
                QPushButton:pressed {{
                    color: #aaaaaa;
                }}
            """)
            self.close_btn.clicked.connect(self.fade_out)
        
        # Размер фиксированный - увеличен на 25% для лучшего отображения многострочного текста
        self.setFixedSize(300, 90)
        
    def resizeEvent(self, event):
        """Позиционируем крестик в левом верхнем углу"""
        super().resizeEvent(event)
        if self.persistent and hasattr(self, 'close_btn'):
            self.close_btn.move(5, 5)
            self.close_btn.raise_()
        
    def setup_animation(self):
        """Настройка анимации появления/исчезновения"""
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(self.animation_duration)
        from PyQt6.QtCore import QEasingCurve
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Таймер для автозакрытия
        self.close_timer = QTimer()
        self.close_timer.setSingleShot(True)
        self.close_timer.timeout.connect(self.fade_out)
        
    def show_notification(self):
        """Показать уведомление с анимацией"""
        from PyQt6.QtCore import QPoint
        
        # Позиция в верхнем правом углу
        screen = QApplication.primaryScreen()
        screen_rect = screen.availableGeometry()
        
        # Конечная позиция (правый верхний угол с отступом)
        x = screen_rect.right() - self.width() - 20
        y = screen_rect.top() + 20
        
        # Стартовая позиция (за экраном сверху)
        start_pos_x = x
        start_pos_y = screen_rect.top() - self.height() - 10
        
        self.move(start_pos_x, start_pos_y)
        
        self.animation.setStartValue(QPoint(start_pos_x, start_pos_y))
        self.animation.setEndValue(QPoint(x, y))
        
        self.show()
        self.raise_()  # Поднимаем на передний план
        self.animation.start()

        # Запуск таймера на автозакрытие (если не persistent)
        if not self.persistent and self.auto_close_time and self.auto_close_time > 0:
            self.close_timer.start(self.auto_close_time)
        
    def fade_out(self):
        """Исчезновение уведомления"""
        from PyQt6.QtCore import QPoint
        
        screen = QApplication.primaryScreen()
        screen_rect = screen.availableGeometry()
        
        current_pos = self.pos()
        end_y = screen_rect.top() - self.height() - 10
        
        self.animation.setStartValue(current_pos)
        self.animation.setEndValue(QPoint(current_pos.x(), end_y))
        self.animation.finished.connect(self.hide)
        self.animation.start()

    def update_theme(self, variant):
        """Обновить тему уведомления"""
        try:
            self.variant = variant
            
            # Обновляем цвета в зависимости от темы
            if self.variant == 'dark':
                bg_color = "rgba(40, 40, 40, 230)"
                text_color = "#ffffff"
                border_color = "rgba(100, 100, 100, 150)"
            else:
                # Для светлой темы
                bg_color = "rgba(255, 255, 255, 240)"
                text_color = "#000000"
                border_color = "rgba(200, 200, 200, 150)"
            
            # Применяем новый стиль к контейнеру
            self.container.setStyleSheet(f"""
                #notificationContainer {{
                    background-color: {bg_color};
                    border-radius: 10px;
                    border: 1px solid {border_color};
                    padding: 15px 15px 15px 15px;
                }}
            """)
            
            # Обновляем стиль текста у всех QLabel внутри контейнера
            for i in range(self.container.layout().count()):
                widget = self.container.layout().itemAt(i).widget()
                if isinstance(widget, QLabel):
                    current_style = widget.styleSheet()
                    # Убираем старый цвет текста и добавляем новый
                    import re
                    # Удаляем старый color из стиля
                    current_style = re.sub(r'color:\s*[^;]+;', '', current_style)
                    # Добавляем новый цвет текста
                    widget.setStyleSheet(current_style + f"color: {text_color}; margin: 0; padding: 0;")
            
            # Обновляем стиль кнопки закрытия, если она есть
            if self.persistent and hasattr(self, 'close_btn'):
                self.close_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {text_color};
                        font-weight: bold;
                        font-size: 14px;
                        border: none;
                        padding: 0;
                        margin: 0;
                    }}
                    QPushButton:hover {{
                        color: #cccccc;
                    }}
                    QPushButton:pressed {{
                        color: #aaaaaa;
                    }}
                """)
            
            # Обновляем отображение
            self.update()
            self.repaint()
            
        except Exception as e:
            print(f"❌ Ошибка обновления темы виджета: {e}")

    def reapply_theme(self):
        """Полностью перерисовать уведомление с новой темой"""
        # Этот метод можно использовать для полного пересоздания виджета
        # Но для простоты будем использовать update_theme
        self.update_theme(self.variant)

    


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
    
    def show_notification(self, notif_type='info', title='', message='', persistent=False, variant='default'):
        """Показать всплывающее уведомление"""
        try:
            # Если variant='default', определяем его на основе текущей темы
            if variant == 'default':
                if hasattr(self.main_window, 'current_theme'):
                    theme = self.main_window.current_theme
                    variant = 'dark' if theme == 'dark' else 'light'
                else:
                    variant = 'dark'
            
            notification = NotificationWidget(
                self.main_window,
                notification_type=notif_type,
                title=title,
                message=message,
                persistent=persistent,
                variant=variant
            )

            notification.show_notification()
            
            # Убедимся, что список существует
            if not hasattr(self, 'notification_widgets'):
                self.notification_widgets = []
            
            self.notification_widgets.append(notification)

            # Безопасное удаление из списка при закрытии
            def on_close():
                try:
                    # Двойная проверка для безопасности
                    if hasattr(self, 'notification_widgets') and notification in self.notification_widgets:
                        self.notification_widgets.remove(notification)
                except (AttributeError, RuntimeError):
                    # Игнорируем ошибки, если объект уже удален
                    pass
                except Exception as e:
                    # Логируем другие ошибки, но не падаем
                    print(f"⚠️ Ошибка в on_close: {e}")

            # Используем прямое соединение, чтобы избежать проблем с очередями
            notification.destroyed.connect(on_close, Qt.ConnectionType.DirectConnection)

            print(f"📬 Уведомление: {title} - {message} (persistent={persistent}, variant={variant})")

        except Exception as e:
            print(f"❌ Ошибка при показе уведомления: {e}")
            import traceback
            traceback.print_exc()
        
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
    
    def check_user_notifications(self, employee_id):
        """Проверить уведомления для конкретного пользователя при входе"""
        try:
            today = QDate.currentDate()
            tomorrow = today.addDays(1)
            
            # Получаем активы пользователя, которые нужно вернуть
            query = """
                SELECT 
                    uh.history_id,
                    a.asset_id,
                    a.name,
                    uh.planned_return_date,
                    uh.actual_return_date
                FROM Usage_History uh
                JOIN Assets a ON uh.asset_id = a.asset_id
                WHERE uh.employee_id = ?
                    AND uh.operation_type = 'выдача'
                    AND uh.actual_return_date IS NULL
                    AND DATE(uh.planned_return_date) <= DATE('now')
                ORDER BY uh.planned_return_date ASC
            """
            
            overdue_results = self.db.execute_query(query, (employee_id,))
            
            for row in overdue_results:
                history_id, asset_id, asset_name, planned_date_str, _ = row
                planned_date = QDate.fromString(planned_date_str, "yyyy-MM-dd")
                
                if planned_date < today:
                    # Просрочено - PERSISTENT (только крестик закрывает)
                    days_overdue = today.daysTo(planned_date)
                    days_overdue = abs(days_overdue)
                    title = '🚨 Просрочка'
                    message = f'{asset_name}\nПросрочка: {days_overdue} дн.'
                    self.show_notification('error', title, message, persistent=True)
                    self._mark_as_overdue(history_id)
                elif planned_date == today:
                    # Сегодня истекает срок - PERSISTENT
                    title = '⚠️ Срок истекает сегодня'
                    message = f'{asset_name}'
                    self.show_notification('error', title, message, persistent=True)
            
            # Проверяем активы, которые нужно вернуть завтра
            query_tomorrow = """
                SELECT 
                    uh.history_id,
                    a.asset_id,
                    a.name,
                    uh.planned_return_date
                FROM Usage_History uh
                JOIN Assets a ON uh.asset_id = a.asset_id
                WHERE uh.employee_id = ?
                    AND uh.operation_type = 'выдача'
                    AND uh.actual_return_date IS NULL
                    AND DATE(uh.planned_return_date) = DATE('now', '+1 day')
                ORDER BY uh.planned_return_date ASC
            """
            
            tomorrow_results = self.db.execute_query(query_tomorrow, (employee_id,))
            
            for row in tomorrow_results:
                history_id, asset_id, asset_name, planned_date_str = row
                title = '⏰ Завтра истекает срок'
                message = f'{asset_name}'
                self.show_notification('warning', title, message)
            
        except Exception as e:
            print(f"❌ Ошибка при проверке уведомлений пользователя: {e}")
    
    def check_admin_overdue(self):
        """Проверить все просрочки в системе и показать админу уведомление"""
        try:
            today = QDate.currentDate()
            
            # Получаем ВСЕ просроченные активы (выданные, но не возвращённые, и срок уже прошёл)
            query = """
                SELECT 
                    uh.history_id,
                    e.last_name || ' ' || e.first_name || COALESCE(' ' || e.patronymic, '') as employee_full_name,
                    a.name,
                    uh.planned_return_date
                FROM Usage_History uh
                JOIN Assets a ON uh.asset_id = a.asset_id
                JOIN Employees e ON uh.employee_id = e.employee_id
                WHERE uh.operation_type = 'выдача'
                    AND uh.actual_return_date IS NULL
                    AND DATE(uh.planned_return_date) < DATE('now')
                ORDER BY uh.planned_return_date ASC
            """
            
            overdue_results = self.db.execute_query(query)
            
            if overdue_results:
                # Собираем список просроченных активов по сотрудникам
                overdue_by_employee = {}
                for row in overdue_results:
                    history_id, employee_name, asset_name, planned_date_str = row
                    planned_date = QDate.fromString(planned_date_str, "yyyy-MM-dd")
                    days_overdue = abs(today.daysTo(planned_date))
                    
                    if employee_name not in overdue_by_employee:
                        overdue_by_employee[employee_name] = []
                    overdue_by_employee[employee_name].append({
                        'asset': asset_name,
                        'days': days_overdue
                    })
                
                # Показываем первое уведомление с первым сотрудником
                first_employee = list(overdue_by_employee.keys())[0]
                first_assets = overdue_by_employee[first_employee]
                
                # Формируем сообщение
                title = '🚨 Обнаружена просрочка!'
                message = f'у сотрудника {first_employee}'
                
                # Если есть несколько просроченных активов у одного сотрудника, добавляем количество
                if len(first_assets) > 1:
                    message += f'\n({len(first_assets)} активов)'
                
                self.show_notification('error', title, message, persistent=True)
                
                # Если есть ещё сотрудники с просрочками, показываем дополнительные уведомления
                for idx, (employee_name, assets) in enumerate(list(overdue_by_employee.items())[1:], 1):
                    # Небольшая задержка между уведомлениями
                    QTimer.singleShot(500 * (idx + 1), lambda name=employee_name, asset_list=assets: 
                        self.show_notification('error', '🚨 Обнаружена просрочка!', 
                                             f'у сотрудника {name}' + (f'\n({len(asset_list)} активов)' if len(asset_list) > 1 else ''),
                                             persistent=True))
            
        except Exception as e:
            print(f"❌ Ошибка при проверке просрочек для админа: {e}")
    
    def check_new_requests_for_admin(self):
        """Проверить новые запросы на выдачу активов и показать уведомление админу"""
        try:
            # Получаем ВСЕ ожидающие одобрения запросы (со статусом 'pending')
            query = """
                SELECT 
                    ar.request_id,
                    e.last_name || ' ' || e.first_name || COALESCE(' ' || e.patronymic, '') as employee_full_name,
                    a.name,
                    ar.request_date
                FROM Asset_Requests ar
                JOIN Assets a ON ar.asset_id = a.asset_id
                JOIN Employees e ON ar.employee_id = e.employee_id
                WHERE ar.status = 'pending'
                ORDER BY ar.request_date ASC
            """
            
            pending_requests = self.db.execute_query(query)
            
            if pending_requests:
                # Собираем запросы по сотрудникам
                requests_by_employee = {}
                for row in pending_requests:
                    request_id, employee_name, asset_name, request_date = row
                    
                    if employee_name not in requests_by_employee:
                        requests_by_employee[employee_name] = []
                    requests_by_employee[employee_name].append({
                        'asset': asset_name,
                        'request_id': request_id
                    })
                
                # Показываем первое уведомление с первым сотрудником
                first_employee = list(requests_by_employee.keys())[0]
                first_requests = requests_by_employee[first_employee]
                
                # Формируем сообщение
                title = '📋 Новый запрос'
                message = f'от {first_employee}'
                
                # Если есть несколько запросов от одного сотрудника, добавляем количество
                if len(first_requests) > 1:
                    message += f'\n({len(first_requests)} запросов)'
                
                self.show_notification('info', title, message, persistent=True)
                
                # Если есть ещё сотрудники с запросами, показываем дополнительные уведомления
                for idx, (employee_name, req_list) in enumerate(list(requests_by_employee.items())[1:], 1):
                    # Небольшая задержка между уведомлениями
                    QTimer.singleShot(500 * (idx + 1), lambda name=employee_name, req_items=req_list: 
                        self.show_notification('info', '📋 Новый запрос', 
                                             f'от {name}' + (f'\n({len(req_items)} запросов)' if len(req_items) > 1 else ''),
                                             persistent=True))
            
        except Exception as e:
            print(f"❌ Ошибка при проверке новых запросов для админа: {e}")
    
    def cleanup(self):
        """Очистка при закрытии приложения"""
        self.stop_checking()
        for widget in self.notification_widgets:
            try:
                widget.close()
            except:
                pass

    ##
    def update_notifications_theme(self):
        """Обновить тему всех открытых уведомлений"""
        try:
            # Определяем текущую тему из главного окна
            if hasattr(self.main_window, 'current_theme'):
                theme = self.main_window.current_theme
                variant = 'dark' if theme == 'dark' else 'light'
            else:
                variant = 'dark'  # По умолчанию тёмная
            
            print(f"🎨 Обновление темы уведомлений на: {variant}")
            
            # Обновляем все открытые уведомления
            for notification in self.notification_widgets[:]:  # Используем копию списка
                try:
                    if hasattr(notification, 'update_theme'):
                        notification.update_theme(variant)
                except Exception as e:
                    print(f"❌ Ошибка обновления темы уведомления: {e}")
                    # Если не удалось обновить, закрываем уведомление
                    if notification in self.notification_widgets:
                        self.notification_widgets.remove(notification)
        except Exception as e:
            print(f"❌ Ошибка в update_notifications_theme: {e}")

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QComboBox, QDateEdit, QPushButton, QMessageBox, QTextEdit)
from PyQt6.QtCore import QDate, QDateTime
from database.db_manager import DatabaseManager
import sys
import os

# Добавляем импорт для аудит-логгера
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from audit_logger import AuditLogger
    AUDIT_ENABLED = True
except ImportError:
    AUDIT_ENABLED = False
    print(" AuditLogger не найден, логирование отключено")


class ReturnDialog(QDialog):
    def __init__(self, parent=None, current_user=None):
        super().__init__(parent)
        self.db = DatabaseManager()
        self.current_user = current_user
        self.is_admin = current_user and current_user.get('role') == 'admin'
        self.setWindowTitle("Возврат актива")
        self.setFixedSize(500, 350)  # Уменьшили высоту
        self.setup_ui()
        self.load_dropdown_data()

    def setup_ui(self):
        """Настройка интерфейса диалога"""
        layout = QVBoxLayout(self)

        # Форма для ввода данных
        form_layout = QFormLayout()

        # Выбор сотрудника (только для админа)
        self.employee_combo = QComboBox()
        self.employee_label = None  # Будет создана, если нужна

        # Выбор актива (только выданные этому сотруднику)
        self.asset_combo = QComboBox()

        # Дата возврата
        self.return_date = QDateEdit()
        self.return_date.setDate(QDate.currentDate())
        self.return_date.setCalendarPopup(True)

        # Комментарий
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)
        self.notes_input.setPlaceholderText("Комментарий к возврату (например: требуется поверка, поврежден...)")

        # Добавляем поля в форму
        if self.is_admin:
            # Для админа показываем выбор сотрудника
            form_layout.addRow("Сотрудник*:", self.employee_combo)
        else:
            # Для обычного пользователя скрываем выбор сотрудника
            pass

        form_layout.addRow("Актив для возврата*:", self.asset_combo)
        form_layout.addRow("Дата возврата*:", self.return_date)
        form_layout.addRow("Комментарий:", self.notes_input)

        layout.addLayout(form_layout)

        # Кнопки
        button_layout = QHBoxLayout()
        self.return_btn = QPushButton("✅ Вернуть")
        self.cancel_btn = QPushButton("❌ Отмена")

        button_layout.addWidget(self.return_btn)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

        # Подключаем кнопки и сигналы
        self.return_btn.clicked.connect(self.return_asset)
        self.cancel_btn.clicked.connect(self.reject)
        if self.is_admin:
            self.employee_combo.currentIndexChanged.connect(self.update_assets_list)

    def load_dropdown_data(self):
        """Загрузка данных для выпадающих списков"""
        try:
            if self.is_admin:
                # Для админа: загружаем всех сотрудников
                employees = self.db.execute_query("""
                    SELECT 
                        employee_id,
                        last_name || ' ' || first_name || ' ' || COALESCE(patronymic, '') as full_name,
                        email
                    FROM Employees 
                    ORDER BY last_name, first_name
                """)

                for employee_id, full_name, email in employees:
                    if email:
                        display_text = f"{full_name} ({email})"
                    else:
                        display_text = full_name
                    self.employee_combo.addItem(display_text, employee_id)
                
                # Инициируем загрузку активов для первого сотрудника
                self.update_assets_list()
            else:
                # Для обычного пользователя: берем его employee_id
                if self.current_user and self.current_user.get('employee_id'):
                    self.update_assets_list()
                else:
                    QMessageBox.critical(self, "Ошибка", "Не удается определить сотрудника!")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки данных: {e}")

    def update_assets_list(self):
        """Обновление списка активов при выборе сотрудника"""
        self.asset_combo.clear()

        # Определяем ID сотрудника
        if self.is_admin:
            employee_id = self.employee_combo.currentData()
        else:
            # Для обычного пользователя используем его ID
            employee_id = self.current_user.get('employee_id') if self.current_user else None

        if not employee_id:
            return

        try:
            # Загружаем активы, выданные этому сотруднику с информацией о количестве
            assets = self.db.execute_query("""
                SELECT a.asset_id, a.name || ' (' || a.model || ') - до ' || uh.planned_return_date, uh.notes
                FROM Assets a
                JOIN Usage_History uh ON a.asset_id = uh.asset_id
                WHERE uh.employee_id = ? 
                  AND uh.operation_type = 'выдача'
                  AND uh.actual_return_date IS NULL
                  AND a.current_status IN ('Выдан', 'Доступен')
                ORDER BY uh.planned_return_date
            """, (employee_id,))

            for asset_id, asset_description, notes in assets:
                # Извлекаем количество из примечаний
                quantity_str = ""
                if notes and "Кол-во выданных:" in notes:
                    quantity_str = " - " + notes
                self.asset_combo.addItem(asset_description + quantity_str, asset_id)

            if not assets:
                self.asset_combo.addItem("⚠️ Нет активов для возврата", None)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки активов: {e}")

    def return_asset(self):
        """Оформление возврата актива"""
        # Проверяем обязательные поля
        if self.is_admin:
            if self.employee_combo.currentData() is None:
                QMessageBox.warning(self, "Ошибка", "Выберите сотрудника!")
                return
            employee_id = self.employee_combo.currentData()
            employee_name = self.employee_combo.currentText().split(' (')[0]
        else:
            # Для обычного пользователя берем его ID
            employee_id = self.current_user.get('employee_id') if self.current_user else None
            if not employee_id:
                QMessageBox.warning(self, "Ошибка", "Не удается определить вашу должность!")
                return
            # Получаем имя сотрудника из БД
            emp_data = self.db.execute_query(
                "SELECT last_name, first_name, patronymic FROM Employees WHERE employee_id = ?",
                (employee_id,)
            )
            if emp_data:
                last_name, first_name, patronymic = emp_data[0]
                employee_name = f"{last_name} {first_name}".strip()
                if patronymic:
                    employee_name += f" {patronymic}"
            else:
                employee_name = "Неизвестный сотрудник"

        if self.asset_combo.currentData() is None:
            QMessageBox.warning(self, "Ошибка", "Выберите актив для возврата!")
            return

        try:
            asset_id = self.asset_combo.currentData()
            # Сохраняем дату возврата с временем для правильной сортировки
            current_datetime = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
            return_date = self.return_date.date().toString("yyyy-MM-dd")
            notes = self.notes_input.toPlainText().strip() or None

            # Получаем информацию для подтверждения
            asset_name = self.asset_combo.currentText().split(' - до')[0]  # Убираем дату возврата

            # Построение сообщения подтверждения
            if self.is_admin:
                confirm_message = f"Вернуть актив:\n{asset_name}\n\nОт сотрудника:\n{employee_name}"
            else:
                confirm_message = f"Вернуть актив:\n{asset_name}"

            # Подтверждение операции
            confirm = QMessageBox.question(
                self,
                "Подтверждение возврата",
                confirm_message,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if confirm != QMessageBox.StandardButton.Yes:
                return

            # Получаем текущее количество и информацию о выданном количестве
            asset_data = self.db.execute_query(
                "SELECT quantity FROM Assets WHERE asset_id = ?",
                (asset_id,)
            )
            current_quantity = asset_data[0][0] if asset_data else 0

            # Получаем записи о выдаче, чтобы узнать сколько было выдано
            issue_records = self.db.execute_query('''
                SELECT notes FROM Usage_History
                WHERE asset_id = ? 
                  AND employee_id = ? 
                  AND operation_type = 'выдача'
                  AND actual_return_date IS NULL
            ''', (asset_id, employee_id))

            quantity_issued = 0
            if issue_records:
                issue_notes = issue_records[0][0] or ""
                # Извлекаем количество из примечаний: "Кол-во выданных: X шт."
                if "Кол-во выданных:" in issue_notes:
                    try:
                        qty_text = issue_notes.split("Кол-во выданных:")[1].split("шт.")[0].strip()
                        quantity_issued = int(qty_text)
                    except (IndexError, ValueError):
                        quantity_issued = 1
                else:
                    quantity_issued = 1

            # Увеличиваем количество при возврате
            new_quantity = current_quantity + quantity_issued
            self.db.execute_update(
                "UPDATE Assets SET quantity = ? WHERE asset_id = ?",
                (new_quantity, asset_id)
            )

            # Обновляем запись в истории (отмечаем дату фактического возврата)
            self.db.execute_update('''
                UPDATE Usage_History 
                SET actual_return_date = ?, notes = ?
                WHERE asset_id = ? 
                  AND employee_id = ? 
                  AND operation_type = 'выдача'
                  AND actual_return_date IS NULL
            ''', (return_date, notes, asset_id, employee_id))
            
            # Обновляем статус актива на основе активных выдач
            self.db.update_asset_status(asset_id)

            # Создаем НОВУЮ запись операции возврата в историю с временем
            return_notes = f"Возврат актива (Кол-во: {quantity_issued} шт.){'. ' + notes if notes else ''}"
            self.db.execute_update('''
                INSERT INTO Usage_History 
                (asset_id, employee_id, operation_type, operation_date, notes)
                VALUES (?, ?, 'возврат', ?, ?)
            ''', (asset_id, employee_id, current_datetime, return_notes))

            # Логирование возврата актива
            if AUDIT_ENABLED and self.current_user:
                AuditLogger.log_action(
                    self.current_user.get('user_id'),
                    self.current_user.get('username'),
                    'asset_returned',
                    {
                        'asset_id': asset_id,
                        'asset_name': asset_name,
                        'employee_id': employee_id,
                        'employee_name': employee_name,
                        'quantity': quantity_issued,
                        'return_date': return_date
                    }
                )

            QMessageBox.information(self, "Успех", f"Актив успешно возвращен!\nКол-во: {quantity_issued} шт.\nОсталось на складе: {new_quantity} шт.")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при возврате актива: {e}")
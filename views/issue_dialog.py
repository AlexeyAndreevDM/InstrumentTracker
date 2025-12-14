from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QComboBox, QDateEdit, QPushButton, QMessageBox, QSpinBox, QLabel)
from PyQt6.QtCore import QDate, QDateTime, QTime
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


class IssueDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseManager()
        self.setWindowTitle("Выдать актив сотруднику")
        self.setFixedSize(450, 350)
        self.setup_ui()
        self.load_dropdown_data()

    def setup_ui(self):
        """Настройка интерфейса диалога"""
        layout = QVBoxLayout(self)

        # Форма для ввода данных
        form_layout = QFormLayout()

        # Выбор сотрудника
        self.employee_combo = QComboBox()

        # Выбор актива (только доступные)
        self.asset_combo = QComboBox()
        self.asset_combo.currentIndexChanged.connect(self.on_asset_changed)

        # Информация о доступном количестве
        self.available_quantity_label = QLabel("Доступно: 0")

        # Количество для выдачи
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 1000)
        self.quantity_spin.setValue(1)

        # Даты
        self.issue_date = QDateEdit()
        self.issue_date.setDate(QDate.currentDate())
        self.issue_date.setCalendarPopup(True)

        self.planned_return_date = QDateEdit()
        self.planned_return_date.setDate(QDate.currentDate().addDays(7))
        self.planned_return_date.setCalendarPopup(True)

        # Добавляем поля в форму
        form_layout.addRow("Сотрудник*:", self.employee_combo)
        form_layout.addRow("Актив*:", self.asset_combo)
        form_layout.addRow("", self.available_quantity_label)
        form_layout.addRow("Количество для выдачи*:", self.quantity_spin)
        form_layout.addRow("Дата выдачи*:", self.issue_date)
        form_layout.addRow("Планируемая дата возврата*:", self.planned_return_date)

        layout.addLayout(form_layout)

        # Кнопки
        button_layout = QHBoxLayout()
        self.issue_btn = QPushButton("✅ Выдать")
        self.cancel_btn = QPushButton("❌ Отмена")

        button_layout.addWidget(self.issue_btn)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

        # Подключаем кнопки
        self.issue_btn.clicked.connect(self.issue_asset)
        self.cancel_btn.clicked.connect(self.reject)

    def load_dropdown_data(self):
        """Загрузка данных для выпадающих списков"""
        try:
            # Загружаем сотрудников - гарантированно уникальные
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

            # Загружаем только доступные активы с количеством
            assets = self.db.execute_query("""
                SELECT a.asset_id, a.name || ' (' || a.model || ')', a.quantity
                FROM Assets a 
                WHERE a.current_status = 'Доступен'
                ORDER BY a.name
            """)

            for asset_id, asset_description, quantity in assets:
                display_text = f"{asset_description} - {quantity} шт."
                self.asset_combo.addItem(display_text, asset_id)

            # Обновляем информацию о доступном количестве для первого актива
            self.on_asset_changed()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки данных: {e}")

    def on_asset_changed(self):
        """Обновление информации о доступном количестве при смене актива"""
        asset_id = self.asset_combo.currentData()
        if asset_id is None:
            self.available_quantity_label.setText("Доступно: 0")
            self.quantity_spin.setMaximum(1)
            return

        try:
            asset_info = self.db.execute_query(
                "SELECT quantity FROM Assets WHERE asset_id = ?",
                (asset_id,)
            )

            if asset_info:
                available_qty = asset_info[0][0]
                self.available_quantity_label.setText(f"Доступно: {available_qty} шт.")
                self.quantity_spin.setMaximum(available_qty)
                self.quantity_spin.setValue(1)
        except Exception as e:
            print(f"Ошибка при обновлении количества: {e}")

    def issue_asset(self):
        """Оформление выдачи актива"""
        # Проверяем обязательные поля
        if self.employee_combo.currentData() is None:
            QMessageBox.warning(self, "Ошибка", "Выберите сотрудника!")
            return

        if self.asset_combo.currentData() is None:
            QMessageBox.warning(self, "Ошибка", "Выберите актив!")
            return

        # Проверяем даты
        if self.planned_return_date.date() <= self.issue_date.date():
            QMessageBox.warning(self, "Ошибка", "Дата возврата должна быть позже даты выдачи!")
            return

        try:
            employee_id = self.employee_combo.currentData()
            asset_id = self.asset_combo.currentData()
            # Сохраняем дату с временем для правильной сортировки
            current_datetime = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
            issue_date = self.issue_date.date().toString("yyyy-MM-dd")
            planned_return = self.planned_return_date.date().toString("yyyy-MM-dd")
            quantity_issued = self.quantity_spin.value()

            # Получаем информацию для подтверждения
            employee_name = self.employee_combo.currentText().split(' (')[0]
            asset_name = self.asset_combo.currentText().split(' - ')[0]

            # Подтверждение операции
            confirm = QMessageBox.question(
                self,
                "Подтверждение выдачи",
                f"Выдать актив:\n{asset_name}\n\nКол-во: {quantity_issued} шт.\nСотруднику:\n{employee_name}\n\nДата возврата: {planned_return}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if confirm != QMessageBox.StandardButton.Yes:
                return

            # Получаем текущее количество
            current_qty = self.db.execute_query(
                "SELECT quantity FROM Assets WHERE asset_id = ?",
                (asset_id,)
            )[0][0]

            # Вычисляем новое количество
            new_quantity = current_qty - quantity_issued

            # Определяем новый статус
            new_status = 'Доступен' if new_quantity > 0 else 'Выдан'

            # Обновляем количество и статус актива
            self.db.execute_update(
                "UPDATE Assets SET quantity = ?, current_status = ? WHERE asset_id = ?",
                (new_quantity, new_status, asset_id)
            )

            # Добавляем запись в историю с информацией о количестве
            notes = f"Кол-во выданных: {quantity_issued} шт."
            self.db.execute_update('''
                INSERT INTO Usage_History 
                (asset_id, employee_id, operation_type, operation_date, planned_return_date, notes) 
                VALUES (?, ?, 'выдача', ?, ?, ?)
            ''', (asset_id, employee_id, current_datetime, planned_return, notes))

            # Логирование выдачи актива
            if AUDIT_ENABLED and hasattr(self.parent(), 'current_user'):
                AuditLogger.log_action(
                    self.parent().current_user.get('user_id'),
                    self.parent().current_user.get('username'),
                    'asset_issued',
                    {
                        'asset_id': asset_id,
                        'asset_name': asset_name,
                        'employee_id': employee_id,
                        'employee_name': employee_name,
                        'quantity': quantity_issued,
                        'planned_return': planned_return
                    }
                )

            QMessageBox.information(self, "Успех", f"Актив успешно выдан сотруднику!\nВыдано: {quantity_issued} шт.\nОсталось: {new_quantity} шт.")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при выдаче актива: {e}")
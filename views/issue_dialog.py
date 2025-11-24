from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QComboBox, QDateEdit, QPushButton, QMessageBox)
from PyQt6.QtCore import QDate
from database.db_manager import DatabaseManager


class IssueDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseManager()
        self.setWindowTitle("Выдать актив сотруднику")
        self.setFixedSize(450, 300)  # Уменьшили высоту, т.к. убрали информационное окно
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

            # Загружаем только доступные активы
            assets = self.db.execute_query("""
                SELECT a.asset_id, a.name || ' (' || a.model || ')' 
                FROM Assets a 
                WHERE a.current_status = 'Доступен'
                ORDER BY a.name
            """)

            for asset_id, asset_description in assets:
                self.asset_combo.addItem(asset_description, asset_id)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки данных: {e}")

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
            issue_date = self.issue_date.date().toString("yyyy-MM-dd")
            planned_return = self.planned_return_date.date().toString("yyyy-MM-dd")

            # Получаем информацию для подтверждения
            employee_name = self.employee_combo.currentText().split(' (')[0]
            asset_name = self.asset_combo.currentText()

            # Подтверждение операции
            confirm = QMessageBox.question(
                self,
                "Подтверждение выдачи",
                f"Выдать актив:\n{asset_name}\n\nСотруднику:\n{employee_name}\n\nДата возврата: {planned_return}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if confirm != QMessageBox.StandardButton.Yes:
                return

            # Обновляем статус актива
            self.db.execute_update(
                "UPDATE Assets SET current_status = 'Выдан' WHERE asset_id = ?",
                (asset_id,)
            )

            # Добавляем запись в историю
            self.db.execute_update('''
                INSERT INTO Usage_History 
                (asset_id, employee_id, operation_type, operation_date, planned_return_date) 
                VALUES (?, ?, 'выдача', ?, ?)
            ''', (asset_id, employee_id, issue_date, planned_return))

            QMessageBox.information(self, "Успех", "Актив успешно выдан сотруднику!")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при выдаче актива: {e}")
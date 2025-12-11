from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLineEdit, QComboBox, QSpinBox, QPushButton,
                             QMessageBox)
from PyQt6.QtCore import Qt
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
    print("⚠️ AuditLogger не найден, логирование отключено")


class AssetDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseManager()
        self.setWindowTitle("Добавить новый актив")
        self.setFixedSize(450, 350)
        self.setup_ui()
        self.load_dropdown_data()

    def setup_ui(self):
        """Настройка интерфейса диалога"""
        layout = QVBoxLayout(self)

        # Форма для ввода данных
        form_layout = QFormLayout()

        # Поля для ввода
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Например: Шуруповерт DeWalt")

        self.type_combo = QComboBox()

        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("Например: DCD777D2")

        self.serial_input = QLineEdit()
        self.serial_input.setPlaceholderText("Только для инструментов")

        # Комбинированный виджет для местоположения с возможностью ввода нового
        location_layout = QHBoxLayout()
        self.location_combo = QComboBox()
        self.location_combo.setEditable(True)
        self.location_combo.setInsertPolicy(QComboBox.InsertPolicy.InsertAtTop)

        self.btn_add_location = QPushButton("+")
        self.btn_add_location.setFixedWidth(30)
        self.btn_add_location.setToolTip("Добавить новое местоположение")

        location_layout.addWidget(self.location_combo)
        location_layout.addWidget(self.btn_add_location)

        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 1000)
        self.quantity_spin.setValue(1)

        # Добавляем поля в форму
        form_layout.addRow("Название*:", self.name_input)
        form_layout.addRow("Тип*:", self.type_combo)
        form_layout.addRow("Модель/Артикул*:", self.model_input)
        form_layout.addRow("Серийный номер:", self.serial_input)
        form_layout.addRow("Местоположение*:", location_layout)
        form_layout.addRow("Количество*:", self.quantity_spin)

        layout.addLayout(form_layout)

        # Кнопки
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить")
        self.cancel_btn = QPushButton("Отмена")

        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

        # Подключаем кнопки
        self.save_btn.clicked.connect(self.save_asset)
        self.cancel_btn.clicked.connect(self.reject)
        self.btn_add_location.clicked.connect(self.add_new_location)

    def load_dropdown_data(self):
        """Загрузка данных для выпадающих списков"""
        try:
            # Загружаем типы активов
            types = self.db.execute_query("SELECT type_id, type_name FROM Asset_Types")
            for type_id, type_name in types:
                self.type_combo.addItem(type_name, type_id)

            # Загружаем местоположения
            locations = self.db.execute_query("SELECT location_id, location_name FROM Locations")
            for location_id, location_name in locations:
                self.location_combo.addItem(location_name, location_id)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки данных: {e}")

    def add_new_location(self):
        """Добавление нового местоположения"""
        current_text = self.location_combo.currentText().strip()
        if not current_text:
            QMessageBox.warning(self, "Ошибка", "Введите название местоположения!")
            return

        try:
            # Проверяем, нет ли уже такого местоположения
            existing = self.db.execute_query(
                "SELECT location_id FROM Locations WHERE location_name = ?",
                (current_text,)
            )

            if existing:
                QMessageBox.information(self, "Информация", "Такое местоположение уже существует!")
                self.location_combo.setCurrentText(current_text)
                return

            # Добавляем новое местоположение с отметкой *
            new_location_name = f"{current_text} *"
            location_id = self.db.execute_update(
                "INSERT INTO Locations (location_name) VALUES (?)",
                (new_location_name,)
            )

            # Обновляем комбобокс
            self.location_combo.addItem(new_location_name, location_id)
            self.location_combo.setCurrentText(new_location_name)

            # Логирование добавления местоположения
            if AUDIT_ENABLED and hasattr(self.parent(), 'current_user'):
                AuditLogger.log_action(
                    self.parent().current_user.get('user_id'),
                    self.parent().current_user.get('username'),
                    'location_added',
                    {'location_name': new_location_name}
                )

            QMessageBox.information(self, "Успех", f"Местоположение '{new_location_name}' успешно добавлено!")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка добавления местоположения: {e}")

    def save_asset(self):
        """Сохранение нового актива в базу данных"""
        # Проверяем обязательные поля
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "Поле 'Название' обязательно для заполнения!")
            return

        if not self.model_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "Поле 'Модель/Артикул' обязательно для заполнения!")
            return

        # Проверяем местоположение
        location_text = self.location_combo.currentText().strip()
        if not location_text:
            QMessageBox.warning(self, "Ошибка", "Поле 'Местоположение' обязательно для заполнения!")
            return

        try:
            # Если местоположение новое (не выбрано из списка), добавляем его
            location_id = self.location_combo.currentData()
            if location_id is None:
                # Это новое местоположение, которого нет в базе
                new_location_name = f"{location_text} *"
                location_id = self.db.execute_update(
                    "INSERT INTO Locations (location_name) VALUES (?)",
                    (new_location_name,)
                )
            else:
                # Проверяем, не изменился ли текст существующего местоположения
                current_location_name = self.location_combo.currentText()
                db_location = self.db.execute_query(
                    "SELECT location_name FROM Locations WHERE location_id = ?",
                    (location_id,)
                )

                if db_location and current_location_name != db_location[0][0]:
                    # Пользователь изменил текст существующей записи - создаем новую
                    new_location_name = f"{current_location_name} *"
                    location_id = self.db.execute_update(
                        "INSERT INTO Locations (location_name) VALUES (?)",
                        (new_location_name,)
                    )

            # Вставляем новый актив
            asset_id = self.db.execute_update('''
                INSERT INTO Assets (name, type_id, model, serial_number, current_status, location_id, quantity)
                VALUES (?, ?, ?, ?, 'Доступен', ?, ?)
            ''', (
                self.name_input.text().strip(),
                self.type_combo.currentData(),
                self.model_input.text().strip(),
                self.serial_input.text().strip() or None,
                location_id,
                self.quantity_spin.value()
            ))

            # Логирование добавления актива
            if AUDIT_ENABLED and hasattr(self.parent(), 'current_user'):
                AuditLogger.log_action(
                    self.parent().current_user.get('user_id'),
                    self.parent().current_user.get('username'),
                    'asset_added',
                    {
                        'asset_id': asset_id,
                        'name': self.name_input.text().strip(),
                        'type': self.type_combo.currentText(),
                        'model': self.model_input.text().strip(),
                        'quantity': self.quantity_spin.value()
                    }
                )

            QMessageBox.information(self, "Успех", "Актив успешно добавлен!")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения: {e}")
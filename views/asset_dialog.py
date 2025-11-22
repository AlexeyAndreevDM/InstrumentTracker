from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLineEdit, QComboBox, QSpinBox, QPushButton,
                             QMessageBox)
from PyQt6.QtCore import Qt
import sqlite3


class AssetDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить новый актив")
        self.setFixedSize(400, 300)
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

        self.location_combo = QComboBox()

        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 1000)
        self.quantity_spin.setValue(1)

        # Добавляем поля в форму
        form_layout.addRow("Название*:", self.name_input)
        form_layout.addRow("Тип*:", self.type_combo)
        form_layout.addRow("Модель/Артикул*:", self.model_input)
        form_layout.addRow("Серийный номер:", self.serial_input)
        form_layout.addRow("Местоположение*:", self.location_combo)
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

    def load_dropdown_data(self):
        """Загрузка данных для выпадающих списков"""
        try:
            conn = sqlite3.connect('inventory.db')
            cursor = conn.cursor()

            # Загружаем типы активов
            cursor.execute("SELECT type_id, type_name FROM Asset_Types")
            types = cursor.fetchall()
            for type_id, type_name in types:
                self.type_combo.addItem(type_name, type_id)

            # Загружаем местоположения
            cursor.execute("SELECT location_id, location_name FROM Locations")
            locations = cursor.fetchall()
            for location_id, location_name in locations:
                self.location_combo.addItem(location_name, location_id)

            conn.close()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки данных: {e}")

    def save_asset(self):
        """Сохранение нового актива в базу данных"""
        # Проверяем обязательные поля
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "Поле 'Название' обязательно для заполнения!")
            return

        if not self.model_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "Поле 'Модель/Артикул' обязательно для заполнения!")
            return

        try:
            conn = sqlite3.connect('inventory.db')
            cursor = conn.cursor()

            # Вставляем новый актив
            cursor.execute('''
                INSERT INTO Assets (name, type_id, model, serial_number, current_status, location_id, quantity)
                VALUES (?, ?, ?, ?, 'Доступен', ?, ?)
            ''', (
                self.name_input.text().strip(),
                self.type_combo.currentData(),
                self.model_input.text().strip(),
                self.serial_input.text().strip() or None,
                self.location_combo.currentData(),
                self.quantity_spin.value()
            ))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Успех", "Актив успешно добавлен!")
            self.accept()  # Закрываем диалог с положительным результатом

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения: {e}")

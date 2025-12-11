from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLineEdit, QComboBox, QSpinBox, QPushButton,
                             QMessageBox, QCheckBox, QGroupBox, QTextEdit)
from PyQt6.QtCore import Qt, QDate
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


class EditAssetDialog(QDialog):
    def __init__(self, asset_id, parent=None):
        super().__init__(parent)
        self.asset_id = asset_id
        self.db = DatabaseManager()
        self.current_issue_info = None
        self.setWindowTitle("Редактировать актив")
        self.setFixedSize(500, 650)
        self.setup_ui()
        self.load_asset_data()
        self.load_dropdown_data()

    def setup_ui(self):
        """Настройка интерфейса диалога"""
        layout = QVBoxLayout(self)

        # Основная информация об активе
        main_group = QGroupBox("Основная информация")
        main_layout = QVBoxLayout(main_group)

        form_layout = QFormLayout()

        # Поля для ввода
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Например: Шуруповерт DeWalt")

        self.type_combo = QComboBox()

        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("Например: DCD777D2")

        self.serial_input = QLineEdit()
        self.serial_input.setPlaceholderText("Только для инструментов")

        # Комбинированный виджет для местоположения
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

        self.status_combo = QComboBox()
        self.status_combo.addItems(["Доступен", "Выдан", "Списан"])

        # Добавляем поля в форму
        form_layout.addRow("Название*:", self.name_input)
        form_layout.addRow("Тип*:", self.type_combo)
        form_layout.addRow("Модель/Артикул*:", self.model_input)
        form_layout.addRow("Серийный номер:", self.serial_input)
        form_layout.addRow("Местоположение*:", location_layout)
        form_layout.addRow("Количество*:", self.quantity_spin)
        form_layout.addRow("Статус:", self.status_combo)

        main_layout.addLayout(form_layout)
        layout.addWidget(main_group)

        # Группа информации о выдаче (показывается только если статус "Выдан")
        self.issue_group = QGroupBox("Информация о выдаче")
        self.issue_layout = QFormLayout(self.issue_group)

        self.employee_combo = QComboBox()

        # Заменяем QLineEdit на QDateEdit для выбора дат
        from PyQt6.QtWidgets import QDateEdit
        self.issue_date_edit = QDateEdit()
        self.issue_date_edit.setCalendarPopup(True)
        self.issue_date_edit.setDate(QDate.currentDate())

        self.planned_return_edit = QDateEdit()
        self.planned_return_edit.setCalendarPopup(True)
        self.planned_return_edit.setDate(QDate.currentDate().addDays(7))

        self.issue_layout.addRow("Сотрудник*:", self.employee_combo)
        self.issue_layout.addRow("Дата выдачи*:", self.issue_date_edit)
        self.issue_layout.addRow("Планируемая дата возврата*:", self.planned_return_edit)

        layout.addWidget(self.issue_group)
        self.issue_group.setVisible(False)

        # Группа списания
        self.write_off_group = QGroupBox("Списание актива")
        write_off_layout = QVBoxLayout(self.write_off_group)

        self.write_off_checkbox = QCheckBox("Списать актив")
        
        # Форма для количества и причины списания
        writeoff_form = QFormLayout()
        
        self.write_off_quantity_spin = QSpinBox()
        self.write_off_quantity_spin.setRange(1, 1000)
        self.write_off_quantity_spin.setValue(1)
        self.write_off_quantity_spin.setVisible(False)
        
        self.write_off_reason = QTextEdit()
        self.write_off_reason.setMaximumHeight(60)
        self.write_off_reason.setPlaceholderText("Укажите причину списания...")
        self.write_off_reason.setVisible(False)

        writeoff_form.addRow("Кол-во для списания:", self.write_off_quantity_spin)
        writeoff_form.addRow("Причина списания:", self.write_off_reason)
        
        write_off_layout.addWidget(self.write_off_checkbox)
        write_off_layout.addLayout(writeoff_form)

        layout.addWidget(self.write_off_group)
        self.write_off_group.setVisible(False)

        # Кнопки
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("💾 Сохранить")
        self.cancel_btn = QPushButton("❌ Отмена")
        self.delete_btn = QPushButton("🗑️ Удалить актив")
        self.delete_btn.setStyleSheet("background-color: #ff6b6b; color: white;")

        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

        # Подключаем кнопки и сигналы
        self.save_btn.clicked.connect(self.save_asset)
        self.cancel_btn.clicked.connect(self.reject)
        self.delete_btn.clicked.connect(self.delete_asset)
        self.btn_add_location.clicked.connect(self.add_new_location)
        self.write_off_checkbox.toggled.connect(self.on_write_off_toggled)
        self.status_combo.currentTextChanged.connect(self.on_status_changed)

    def load_asset_data(self):
        """Загрузка данных текущего актива"""
        try:
            asset_data = self.db.execute_query("""
                SELECT name, type_id, model, serial_number, location_id, quantity, current_status
                FROM Assets WHERE asset_id = ?
            """, (self.asset_id,))

            if asset_data:
                name, type_id, model, serial_number, location_id, quantity, status = asset_data[0]

                self.name_input.setText(name)
                self.model_input.setText(model)
                self.serial_input.setText(serial_number or "")
                self.quantity_spin.setValue(quantity)
                self.status_combo.setCurrentText(status)

                # Сохраняем ID для дальнейшего использования
                self.current_type_id = type_id
                self.current_location_id = location_id

                # Загружаем информацию о выдаче, если актив выдан
                if status == "Выдан":
                    self.load_issue_info()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки данных актива: {e}")

    def load_issue_info(self):
        """Загрузка информации о текущей выдаче актива"""
        try:
            issue_data = self.db.execute_query("""
                SELECT 
                    e.employee_id,
                    e.last_name || ' ' || e.first_name || ' ' || COALESCE(e.patronymic, '') as employee_name,
                    uh.operation_date,
                    uh.planned_return_date
                FROM Usage_History uh
                JOIN Employees e ON uh.employee_id = e.employee_id
                WHERE uh.asset_id = ? 
                    AND uh.operation_type = 'выдача' 
                    AND uh.actual_return_date IS NULL
                ORDER BY uh.operation_date DESC
                LIMIT 1
            """, (self.asset_id,))

            if issue_data:
                employee_id, employee_name, operation_date, planned_return_date = issue_data[0]
                self.current_issue_info = {
                    'employee_id': employee_id,
                    'employee_name': employee_name,
                    'operation_date': operation_date,
                    'planned_return_date': planned_return_date
                }

        except Exception as e:
            print(f"Ошибка загрузки информации о выдаче: {e}")

    def load_dropdown_data(self):
        """Загрузка данных для выпадающих списков"""
        try:
            # Загружаем типы активов
            types = self.db.execute_query("SELECT type_id, type_name FROM Asset_Types")
            for type_id, type_name in types:
                self.type_combo.addItem(type_name, type_id)
                if hasattr(self, 'current_type_id') and type_id == self.current_type_id:
                    self.type_combo.setCurrentText(type_name)

            # Загружаем местоположения
            locations = self.db.execute_query("SELECT location_id, location_name FROM Locations")
            for location_id, location_name in locations:
                self.location_combo.addItem(location_name, location_id)
                if hasattr(self, 'current_location_id') and location_id == self.current_location_id:
                    self.location_combo.setCurrentText(location_name)

            # Загружаем сотрудников для информации о выдаче
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

            # Устанавливаем текущего сотрудника, если актив выдан
            if self.current_issue_info:
                for i in range(self.employee_combo.count()):
                    if self.employee_combo.itemData(i) == self.current_issue_info['employee_id']:
                        self.employee_combo.setCurrentIndex(i)
                        break

                # Устанавливаем даты из базы данных
                if self.current_issue_info['operation_date']:
                    issue_date = QDate.fromString(self.current_issue_info['operation_date'], 'yyyy-MM-dd')
                    self.issue_date_edit.setDate(issue_date)

                if self.current_issue_info['planned_return_date']:
                    return_date = QDate.fromString(self.current_issue_info['planned_return_date'], 'yyyy-MM-dd')
                    self.planned_return_edit.setDate(return_date)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки данных: {e}")

    def on_status_changed(self, status):
        """Обработчик изменения статуса"""
        # Показываем/скрываем группу списания
        if status == "Списан":
            self.write_off_group.setVisible(True)
            self.write_off_checkbox.setChecked(True)
            self.write_off_quantity_spin.setMaximum(self.quantity_spin.value())
        else:
            self.write_off_group.setVisible(False)
            self.write_off_checkbox.setChecked(False)

        # Показываем/скрываем группу информации о выдаче
        if status == "Выдан":
            self.issue_group.setVisible(True)
        else:
            self.issue_group.setVisible(False)

    def on_write_off_toggled(self, checked):
        """Обработчик переключения чекбокса списания"""
        self.write_off_reason.setVisible(checked)
        self.write_off_quantity_spin.setVisible(checked)
        if checked:
            # Устанавливаем максимальное количество = текущему количеству
            self.write_off_quantity_spin.setMaximum(self.quantity_spin.value())

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

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка добавления местоположения: {e}")

    def save_asset(self):
        """Сохранение изменений актива"""
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

        # Если актив выдан, проверяем обязательные поля выдачи
        if self.status_combo.currentText() == "Выдан":
            if self.employee_combo.currentData() is None:
                QMessageBox.warning(self, "Ошибка", "Выберите сотрудника, которому выдан актив!")
                return

            # Проверяем, что дата возврата позже даты выдачи
            if self.planned_return_edit.date() <= self.issue_date_edit.date():
                QMessageBox.warning(self, "Ошибка", "Дата возврата должна быть позже даты выдачи!")
                return

        # Если актив списывается, проверяем причину
        if self.write_off_checkbox.isChecked() and not self.write_off_reason.toPlainText().strip():
            QMessageBox.warning(self, "Ошибка", "Укажите причину списания!")
            return

        try:
            # Если местоположение новое, добавляем его
            location_id = self.location_combo.currentData()
            if location_id is None:
                new_location_name = f"{location_text} *"
                location_id = self.db.execute_update(
                    "INSERT INTO Locations (location_name) VALUES (?)",
                    (new_location_name,)
                )

            # Получаем старые данные для логирования изменений
            old_data = self.db.execute_query(
                "SELECT name, type_id, model, serial_number, location_id, quantity, current_status FROM Assets WHERE asset_id = ?",
                (self.asset_id,)
            )
            
            old_name, old_type_id, old_model, old_serial, old_location_id, old_quantity, old_status = old_data[0]
            
            # Получаем названия типов и местоположений для логирования
            old_type_name = self.db.execute_query(
                "SELECT type_name FROM Asset_Types WHERE type_id = ?",
                (old_type_id,)
            )[0][0] if old_type_id else "Неизвестно"
            
            old_location_name = self.db.execute_query(
                "SELECT location_name FROM Locations WHERE location_id = ?",
                (old_location_id,)
            )[0][0] if old_location_id else "Неизвестно"

            # Обновляем данные актива
            self.db.execute_update('''
                UPDATE Assets 
                SET name = ?, type_id = ?, model = ?, serial_number = ?, 
                    location_id = ?, quantity = ?, current_status = ?
                WHERE asset_id = ?
            ''', (
                self.name_input.text().strip(),
                self.type_combo.currentData(),
                self.model_input.text().strip(),
                self.serial_input.text().strip() or None,
                location_id,
                self.quantity_spin.value(),
                self.status_combo.currentText(),
                self.asset_id
            ))

            # Обрабатываем операцию выдачи, если актив выдан
            if self.status_combo.currentText() == "Выдан":
                employee_id = self.employee_combo.currentData()
                issue_date = self.issue_date_edit.date().toString('yyyy-MM-dd')
                planned_return_date = self.planned_return_edit.date().toString('yyyy-MM-dd')

                # Получаем имя сотрудника для логирования
                employee_name = self.employee_combo.currentText().split(' (')[0]

                # Проверяем, есть ли уже открытая выдача
                existing_issue = self.db.execute_query('''
                    SELECT history_id FROM Usage_History 
                    WHERE asset_id = ? AND operation_type = 'выдача' AND actual_return_date IS NULL
                ''', (self.asset_id,))

                if existing_issue:
                    # Обновляем существующую выдачу
                    self.db.execute_update('''
                        UPDATE Usage_History 
                        SET employee_id = ?, operation_date = ?, planned_return_date = ?
                        WHERE asset_id = ? AND operation_type = 'выдача' AND actual_return_date IS NULL
                    ''', (employee_id, issue_date, planned_return_date, self.asset_id))
                else:
                    # Создаем новую выдачу
                    self.db.execute_update('''
                        INSERT INTO Usage_History 
                        (asset_id, employee_id, operation_type, operation_date, planned_return_date) 
                        VALUES (?, ?, 'выдача', ?, ?)
                    ''', (self.asset_id, employee_id, issue_date, planned_return_date))

            # Если актив списан, добавляем запись в историю
            if self.write_off_checkbox.isChecked():
                # Для списания используем первого доступного сотрудника (системный учёт)
                employee_for_writeoff = self.db.execute_query(
                    "SELECT employee_id FROM Employees LIMIT 1"
                )
                employee_id = employee_for_writeoff[0][0] if employee_for_writeoff else 1
                
                quantity_to_writeoff = self.write_off_quantity_spin.value()
                current_qty = self.quantity_spin.value()
                new_quantity = current_qty - quantity_to_writeoff
                
                # Обновляем количество при списании
                if new_quantity > 0:
                    # Если остаток остается, статус остается 'Доступен'
                    self.db.execute_update(
                        "UPDATE Assets SET quantity = ?, current_status = 'Доступен' WHERE asset_id = ?",
                        (new_quantity, self.asset_id)
                    )
                else:
                    # Если это последнее количество, устанавливаем 'Списан'
                    self.db.execute_update(
                        "UPDATE Assets SET quantity = 0, current_status = 'Списан' WHERE asset_id = ?",
                        (self.asset_id,)
                    )
                
                writeoff_notes = f"Списано: {quantity_to_writeoff} шт. Причина: {self.write_off_reason.toPlainText().strip()}"
                self.db.execute_update('''
                    INSERT INTO Usage_History 
                    (asset_id, employee_id, operation_type, operation_date, notes) 
                    VALUES (?, ?, 'списание', datetime('now'), ?)
                ''', (self.asset_id, employee_id, writeoff_notes))

            # Логирование редактирования актива
            if AUDIT_ENABLED and hasattr(self.parent(), 'current_user'):
                # Собираем изменения
                changes = {}
                if self.name_input.text().strip() != old_name:
                    changes['name'] = {'old': old_name, 'new': self.name_input.text().strip()}
                if self.type_combo.currentData() != old_type_id:
                    changes['type'] = {'old': old_type_name, 'new': self.type_combo.currentText()}
                if self.model_input.text().strip() != old_model:
                    changes['model'] = {'old': old_model, 'new': self.model_input.text().strip()}
                if self.serial_input.text().strip() != (old_serial or ""):
                    changes['serial'] = {'old': old_serial or "", 'new': self.serial_input.text().strip()}
                if location_id != old_location_id:
                    new_location_name = self.db.execute_query(
                        "SELECT location_name FROM Locations WHERE location_id = ?",
                        (location_id,)
                    )[0][0] if location_id else "Неизвестно"
                    changes['location'] = {'old': old_location_name, 'new': new_location_name}
                if self.quantity_spin.value() != old_quantity:
                    changes['quantity'] = {'old': old_quantity, 'new': self.quantity_spin.value()}
                if self.status_combo.currentText() != old_status:
                    changes['status'] = {'old': old_status, 'new': self.status_combo.currentText()}
                
                if changes:  # Логируем только если были изменения
                    AuditLogger.log_action(
                        self.parent().current_user.get('user_id'),
                        self.parent().current_user.get('username'),
                        'asset_edited',
                        {
                            'asset_id': self.asset_id,
                            'asset_name': self.name_input.text().strip(),
                            'changes': changes
                        }
                    )

            QMessageBox.information(self, "Успех", "Данные актива успешно обновлены!")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения: {e}")

    def delete_asset(self):
        """Удаление актива"""
        confirm = QMessageBox.question(
            self,
            "Подтверждение удаления",
            "Вы уверены, что хотите удалить этот актив?\n\nЭто действие нельзя отменить!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            # Получаем информацию об активе для логирования
            asset_info = self.db.execute_query(
                "SELECT name, model, quantity FROM Assets WHERE asset_id = ?",
                (self.asset_id,)
            )
            
            if not asset_info:
                QMessageBox.warning(self, "Ошибка", "Актив не найден!")
                return
                
            asset_name, asset_model, asset_quantity = asset_info[0]

            # Проверяем, не выдан ли актив
            asset_status = self.db.execute_query(
                "SELECT current_status FROM Assets WHERE asset_id = ?",
                (self.asset_id,)
            )

            if asset_status and asset_status[0][0] == "Выдан":
                QMessageBox.warning(
                    self,
                    "Ошибка",
                    "Нельзя удалить актив со статусом 'Выдан'!\n\nСначала верните актив на склад."
                )
                return

            # Удаляем актив
            self.db.execute_update("DELETE FROM Assets WHERE asset_id = ?", (self.asset_id,))

            # Также удаляем связанные записи в истории
            self.db.execute_update("DELETE FROM Usage_History WHERE asset_id = ?", (self.asset_id,))

            # Логирование удаления актива
            if AUDIT_ENABLED and hasattr(self.parent(), 'current_user'):
                AuditLogger.log_action(
                    self.parent().current_user.get('user_id'),
                    self.parent().current_user.get('username'),
                    'asset_deleted',
                    {
                        'asset_id': self.asset_id,
                        'asset_name': asset_name,
                        'model': asset_model,
                        'quantity': asset_quantity
                    }
                )

            QMessageBox.information(self, "Успех", "Актив успешно удален!")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка удаления: {e}")
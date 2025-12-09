from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QComboBox, QPushButton, QMessageBox, QDateEdit, QTextEdit, QSpinBox)
from PyQt6.QtCore import Qt, QDate
from database.db_manager import DatabaseManager


class RequestAssetDialog(QDialog):
    """Диалог для создания запроса на выдачу актива"""
    
    def __init__(self, current_user, parent=None):
        super().__init__(parent)
        self.db = DatabaseManager()
        self.current_user = current_user
        
        self.setWindowTitle("📝 Запросить актив")
        self.setFixedSize(500, 400)
        
        self.init_ui()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Актив
        asset_label = QLabel("🔧 Выберите актив:")
        layout.addWidget(asset_label)
        
        self.asset_combo = QComboBox()
        self.load_available_assets()
        layout.addWidget(self.asset_combo)
        
        # Дата плановой выдачи
        date_label = QLabel("📅 Сегодня:")
        layout.addWidget(date_label)
        
        self.issue_date = QDateEdit()
        self.issue_date.setDate(QDate.currentDate())
        self.issue_date.setReadOnly(True)
        layout.addWidget(self.issue_date)
        
        # Дата планового возврата
        return_label = QLabel("📅 Плановая дата возврата:")
        layout.addWidget(return_label)
        
        self.return_date = QDateEdit()
        self.return_date.setDate(QDate.currentDate().addDays(7))  # По умолчанию через неделю
        self.return_date.setCalendarPopup(True)
        layout.addWidget(self.return_date)
        
        # Примечание
        notes_label = QLabel("📝 Примечание:")
        layout.addWidget(notes_label)
        
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Введите причину запроса или дополнительную информацию...")
        self.notes_input.setMaximumHeight(80)
        layout.addWidget(self.notes_input)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        submit_btn = QPushButton("✅ Отправить запрос")
        submit_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        submit_btn.clicked.connect(self.submit_request)
        buttons_layout.addWidget(submit_btn)
        
        cancel_btn = QPushButton("❌ Отмена")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def load_available_assets(self):
        """Загрузка списка доступных активов"""
        try:
            query = """
            SELECT a.asset_id, a.name || ' (' || at.type_name || ')', a.quantity
            FROM Assets a
            JOIN Asset_Types at ON a.type_id = at.type_id
            WHERE a.quantity > 0 AND a.current_status != 'Списан'
            ORDER BY a.name
            """
            assets = self.db.execute_query(query)
            
            self.asset_combo.clear()
            self.asset_combo.addItem("-- Выберите актив --", None)
            
            for asset_id, asset_name, quantity in assets:
                display_text = f"{asset_name} (доступно: {quantity})"
                self.asset_combo.addItem(display_text, asset_id)
        
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки активов:\n{str(e)}")
    
    def submit_request(self):
        """Отправка запроса на выдачу актива"""
        asset_id = self.asset_combo.currentData()
        
        if not asset_id:
            QMessageBox.warning(self, "Ошибка", "Выберите актив!")
            return
        
        return_date = self.return_date.date().toString("yyyy-MM-dd")
        notes = self.notes_input.toPlainText().strip()
        
        if not self.current_user.get('employee_id'):
            QMessageBox.warning(self, "Ошибка", "Не указан ID сотрудника!")
            return
        
        try:
            # Создаем запрос на выдачу
            query = """
            INSERT INTO Asset_Requests (asset_id, employee_id, request_date, planned_return_date, notes, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            
            self.db.execute_update(
                query,
                (
                    asset_id,
                    self.current_user.get('employee_id'),
                    datetime.now().isoformat(),
                    return_date,
                    notes,
                    'pending'
                )
            )
            
            QMessageBox.information(
                self,
                "Успех",
                "✅ Запрос на выдачу актива отправлен администратору!"
            )
            
            self.accept()
        
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании запроса:\n{str(e)}")

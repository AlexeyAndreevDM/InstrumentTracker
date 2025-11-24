import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTableView, QVBoxLayout,
                             QWidget, QPushButton, QMessageBox, QHBoxLayout, QDialog,
                             QTabWidget)  # Добавили QTabWidget
from PyQt6.QtSql import QSqlDatabase, QSqlQueryModel
from PyQt6.QtCore import Qt

from views.asset_dialog import AssetDialog
from views.issue_dialog import IssueDialog  # Новый импорт
from views.return_dialog import ReturnDialog  # Новый импорт
from database.db_manager import DatabaseManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.init_ui()
        self.load_assets_data()

    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        self.setWindowTitle("Система учета инструментов и расходников - АО КОНСИСТ-ОС")
        self.setGeometry(100, 100, 1200, 700)

        # Центральный виджет с вкладками
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Основной layout
        layout = QVBoxLayout(central_widget)

        # Создаем вкладки
        self.tabs = QTabWidget()

        # Вкладка 1: Каталог активов
        self.assets_tab = QWidget()
        self.setup_assets_tab()
        self.tabs.addTab(self.assets_tab, "📋 Каталог активов")

        # Вкладка 2: Операции
        self.operations_tab = QWidget()
        self.setup_operations_tab()
        self.tabs.addTab(self.operations_tab, "🔄 Операции")

        layout.addWidget(self.tabs)

    def setup_assets_tab(self):
        """Настройка вкладки каталога активов"""
        layout = QVBoxLayout(self.assets_tab)

        # Панель кнопок
        buttons_layout = QHBoxLayout()

        self.btn_add = QPushButton("➕ Добавить актив")
        self.btn_edit = QPushButton("✏️ Редактировать")
        self.btn_delete = QPushButton("🗑️ Удалить")
        self.btn_refresh = QPushButton("🔄 Обновить")

        buttons_layout.addWidget(self.btn_add)
        buttons_layout.addWidget(self.btn_edit)
        buttons_layout.addWidget(self.btn_delete)
        buttons_layout.addWidget(self.btn_refresh)
        buttons_layout.addStretch()

        layout.addLayout(buttons_layout)

        # Таблица активов
        self.assets_table = QTableView()
        layout.addWidget(self.assets_table)

        # Подключаем кнопки
        self.btn_refresh.clicked.connect(self.load_assets_data)
        self.btn_add.clicked.connect(self.add_asset)

    def setup_operations_tab(self):
        """Настройка вкладки операций"""
        layout = QVBoxLayout(self.operations_tab)

        # Панель кнопок операций
        operations_layout = QHBoxLayout()

        self.btn_issue = QPushButton("📤 Выдать актив")
        self.btn_return = QPushButton("📥 Вернуть актив")
        self.btn_history = QPushButton("📊 История операций")

        operations_layout.addWidget(self.btn_issue)
        operations_layout.addWidget(self.btn_return)
        operations_layout.addWidget(self.btn_history)
        operations_layout.addStretch()

        layout.addLayout(operations_layout)

        # Таблица для истории операций (пока пустая)
        self.history_table = QTableView()
        layout.addWidget(self.history_table)

        # Подключаем кнопки
        self.btn_issue.clicked.connect(self.issue_asset)
        self.btn_return.clicked.connect(self.return_asset)
        self.btn_history.clicked.connect(self.load_history_data)

    def load_assets_data(self):
        """Загрузка данных об активах"""
        if not hasattr(self, 'db_connection'):
            self.db_connection = QSqlDatabase.addDatabase("QSQLITE")
            self.db_connection.setDatabaseName("inventory.db")

        if not self.db_connection.isOpen():
            if not self.db_connection.open():
                QMessageBox.critical(self, "Ошибка", "Не удалось подключиться к базе данных!")
                return

        model = QSqlQueryModel()

        query = """
        SELECT 
            a.asset_id as 'ID',
            a.name as 'Название',
            at.type_name as 'Тип',
            a.model as 'Модель',
            a.serial_number as 'Серийный номер',
            a.current_status as 'Статус',
            l.location_name as 'Местоположение',
            a.quantity as 'Количество'
        FROM Assets a
        JOIN Asset_Types at ON a.type_id = at.type_id
        JOIN Locations l ON a.location_id = l.location_id
        ORDER BY a.asset_id
        """

        model.setQuery(query)
        self.assets_table.setModel(model)
        self.assets_table.resizeColumnsToContents()

    def load_history_data(self):
        """Загрузка истории операций"""
        if not hasattr(self, 'db_connection'):
            return

        model = QSqlQueryModel()

        query = """
        SELECT 
            uh.history_id as 'ID',
            e.last_name || ' ' || e.first_name as 'Сотрудник',
            a.name as 'Актив',
            uh.operation_type as 'Тип операции',
            uh.operation_date as 'Дата операции',
            uh.planned_return_date as 'План возврата',
            uh.actual_return_date as 'Факт возврата',
            uh.notes as 'Примечания'
        FROM Usage_History uh
        JOIN Employees e ON uh.employee_id = e.employee_id
        JOIN Assets a ON uh.asset_id = a.asset_id
        ORDER BY uh.operation_date DESC
        """

        model.setQuery(query)
        self.history_table.setModel(model)
        self.history_table.resizeColumnsToContents()

    def add_asset(self):
        """Добавление нового актива"""
        dialog = AssetDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_assets_data()
            QMessageBox.information(self, "Успех", "Новый актив успешно добавлен в систему!")

    def issue_asset(self):
        """Выдача актива сотруднику"""
        dialog = IssueDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_assets_data()
            QMessageBox.information(self, "Успех", "Актив успешно выдан!")

    def return_asset(self):
        """Возврат актива"""
        dialog = ReturnDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_assets_data()
            QMessageBox.information(self, "Успех", "Актив успешно возвращен!")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
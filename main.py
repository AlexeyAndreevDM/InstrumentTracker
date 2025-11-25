import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTableView, QVBoxLayout,
                             QWidget, QPushButton, QMessageBox, QHBoxLayout, QDialog,
                             QTabWidget, QLabel, QDateEdit, QComboBox)
from PyQt6.QtSql import QSqlDatabase, QSqlQueryModel, QSqlQuery
from PyQt6.QtCore import Qt, QDate

from views.asset_dialog import AssetDialog
from views.issue_dialog import IssueDialog
from views.return_dialog import ReturnDialog
from views.edit_asset_dialog import EditAssetDialog
from database.db_manager import DatabaseManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        print("🚀 Инициализация главного окна...")
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

        print("✅ Интерфейс инициализирован")

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
        self.assets_table.doubleClicked.connect(self.edit_asset)
        layout.addWidget(self.assets_table)

        # Подключаем кнопки
        self.btn_refresh.clicked.connect(self.load_assets_data)
        self.btn_add.clicked.connect(self.add_asset)
        self.btn_edit.clicked.connect(self.edit_asset)
        self.btn_delete.clicked.connect(self.delete_asset)

    def setup_operations_tab(self):
        """Настройка вкладки операций"""
        layout = QVBoxLayout(self.operations_tab)

        # Панель фильтров истории
        filter_layout = QHBoxLayout()

        self.history_employee_filter = QComboBox()
        self.history_employee_filter.addItem("Все сотрудники", None)

        self.history_operation_filter = QComboBox()
        self.history_operation_filter.addItem("Все операции", None)
        self.history_operation_filter.addItem("Выдача", "выдача")
        self.history_operation_filter.addItem("Возврат", "возврат")
        self.history_operation_filter.addItem("Списание", "списание")

        self.history_date_from = QDateEdit()
        self.history_date_from.setDate(QDate.currentDate().addDays(-30))
        self.history_date_from.setCalendarPopup(True)

        self.history_date_to = QDateEdit()
        self.history_date_to.setDate(QDate.currentDate())
        self.history_date_to.setCalendarPopup(True)

        self.btn_apply_filters = QPushButton("🔍 Применить фильтры")
        self.btn_clear_filters = QPushButton("❌ Сбросить")

        filter_layout.addWidget(QLabel("Сотрудник:"))
        filter_layout.addWidget(self.history_employee_filter)
        filter_layout.addWidget(QLabel("Операция:"))
        filter_layout.addWidget(self.history_operation_filter)
        filter_layout.addWidget(QLabel("С:"))
        filter_layout.addWidget(self.history_date_from)
        filter_layout.addWidget(QLabel("По:"))
        filter_layout.addWidget(self.history_date_to)
        filter_layout.addWidget(self.btn_apply_filters)
        filter_layout.addWidget(self.btn_clear_filters)
        filter_layout.addStretch()

        layout.addLayout(filter_layout)

        # Панель кнопок операций
        operations_layout = QHBoxLayout()

        self.btn_issue = QPushButton("📤 Выдать актив")
        self.btn_return = QPushButton("📥 Вернуть актив")
        self.btn_history = QPushButton("🔄 Обновить историю")

        operations_layout.addWidget(self.btn_issue)
        operations_layout.addWidget(self.btn_return)
        operations_layout.addWidget(self.btn_history)
        operations_layout.addStretch()

        layout.addLayout(operations_layout)

        # Таблица для истории операций
        self.history_table = QTableView()
        layout.addWidget(self.history_table)

        # Подключаем кнопки
        self.btn_issue.clicked.connect(self.issue_asset)
        self.btn_return.clicked.connect(self.return_asset)
        self.btn_history.clicked.connect(self.load_history_data)
        self.btn_apply_filters.clicked.connect(self.load_history_data)
        self.btn_clear_filters.clicked.connect(self.clear_history_filters)

        # Загружаем данные для фильтров
        self.load_history_filters_data()

    def load_assets_data(self):
        """Загрузка данных об активах"""
        print("🔄 Загрузка данных об активах...")

        if not hasattr(self, 'db_connection'):
            self.db_connection = QSqlDatabase.addDatabase("QSQLITE")
            self.db_connection.setDatabaseName("inventory.db")

        if not self.db_connection.isOpen():
            if not self.db_connection.open():
                error = self.db_connection.lastError().text()
                print(f"❌ Ошибка подключения к базе: {error}")
                QMessageBox.critical(self, "Ошибка", f"Не удалось подключиться к базе данных!\n{error}")
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

        if model.lastError().isValid():
            error = model.lastError().text()
            print(f"❌ Ошибка выполнения запроса: {error}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки данных:\n{error}")
        else:
            row_count = model.rowCount()
            print(f"✅ Данные загружены. Найдено записей: {row_count}")

            if row_count == 0:
                print("⚠️ В базе данных нет записей.")

        self.assets_table.setModel(model)
        self.assets_table.resizeColumnsToContents()

    def load_history_data(self):
        """Загрузка истории операций с фильтрами"""
        print("🔄 Загрузка истории операций...")

        if not hasattr(self, 'db_connection'):
            return

        model = QSqlQueryModel()

        # Базовый запрос
        query = """
        SELECT 
            uh.history_id as 'ID',
            e.last_name || ' ' || e.first_name as 'Сотрудник',
            a.name as 'Актив',
            a.model as 'Модель',
            CASE 
                WHEN uh.operation_type = 'выдача' THEN '📤 Выдача'
                WHEN uh.operation_type = 'возврат' THEN '📥 Возврат'
                WHEN uh.operation_type = 'списание' THEN '🗑️ Списание'
                ELSE uh.operation_type
            END as 'Тип операции',
            uh.operation_date as 'Дата операции',
            uh.planned_return_date as 'План возврата',
            uh.actual_return_date as 'Факт возврата',
            uh.notes as 'Примечания'
        FROM Usage_History uh
        JOIN Employees e ON uh.employee_id = e.employee_id
        JOIN Assets a ON uh.asset_id = a.asset_id
        WHERE 1=1
        """

        params = []

        # Применяем фильтры
        employee_filter = self.history_employee_filter.currentData()
        if employee_filter is not None:
            query += " AND uh.employee_id = ?"
            params.append(employee_filter)

        operation_filter = self.history_operation_filter.currentData()
        if operation_filter is not None:
            query += " AND uh.operation_type = ?"
            params.append(operation_filter)

        date_from = self.history_date_from.date().toString("yyyy-MM-dd")
        date_to = self.history_date_to.date().toString("yyyy-MM-dd")
        query += " AND DATE(uh.operation_date) BETWEEN ? AND ?"
        params.extend([date_from, date_to])

        query += " ORDER BY uh.operation_date DESC"

        # Выполняем запрос
        query_obj = QSqlQuery(self.db_connection)
        query_obj.prepare(query)

        for param in params:
            query_obj.addBindValue(param)

        if not query_obj.exec():
            error = query_obj.lastError().text()
            print(f"❌ Ошибка загрузки истории: {error}")
        else:
            model.setQuery(query_obj)
            print(f"✅ История загружена. Записей: {model.rowCount()}")

        self.history_table.setModel(model)
        self.history_table.resizeColumnsToContents()

    def load_history_filters_data(self):
        """Загрузка данных для фильтров истории"""
        try:
            employees = self.db.execute_query("""
                SELECT employee_id, last_name || ' ' || first_name as full_name
                FROM Employees 
                ORDER BY last_name, first_name
            """)

            for employee_id, full_name in employees:
                self.history_employee_filter.addItem(full_name, employee_id)

        except Exception as e:
            print(f"Ошибка загрузки фильтров истории: {e}")

    def clear_history_filters(self):
        """Сброс фильтров истории"""
        self.history_employee_filter.setCurrentIndex(0)
        self.history_operation_filter.setCurrentIndex(0)
        self.history_date_from.setDate(QDate.currentDate().addDays(-30))
        self.history_date_to.setDate(QDate.currentDate())
        self.load_history_data()

    def get_selected_asset_id(self):
        """Получение ID выбранного актива"""
        # Получаем текущую выбранную строку
        current_index = self.assets_table.currentIndex()
        if not current_index.isValid():
            QMessageBox.warning(self, "Ошибка", "Выберите актив из таблицы!")
            return None

        # Получаем модель и данные из первой колонки (ID)
        model = self.assets_table.model()
        row = current_index.row()
        index_id = model.index(row, 0)  # Первая колонка - ID
        asset_id = model.data(index_id)

        return asset_id

    def add_asset(self):
        """Добавление нового актива"""
        print("➕ Открытие диалога добавления актива...")
        dialog = AssetDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_assets_data()

    def edit_asset(self):
        """Редактирование выбранного актива"""
        print("✏️ Попытка редактирования актива...")
        asset_id = self.get_selected_asset_id()
        if asset_id is None:
            return

        print(f"📝 Редактирование актива ID: {asset_id}")
        dialog = EditAssetDialog(asset_id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            print("✅ Актив успешно отредактирован")
            self.load_assets_data()

    def delete_asset(self):
        """Удаление выбранного актива"""
        print("🗑️ Попытка удаления актива...")
        asset_id = self.get_selected_asset_id()
        if asset_id is None:
            return

        print(f"🗑️ Удаление актива ID: {asset_id}")

        # Создаем диалог для удаления
        dialog = EditAssetDialog(asset_id, self)

        # Подключаемся к сигналу закрытия диалога
        dialog.finished.connect(lambda result: self.on_asset_dialog_finished(result, asset_id))

        # Показываем диалог - пользователь сам нажмет кнопку удаления внутри диалога
        dialog.exec()

    def on_asset_dialog_finished(self, result, asset_id):
        """Обработчик завершения работы диалога редактирования/удаления"""
        if result == QDialog.DialogCode.Accepted:
            print("✅ Операция с активом завершена, обновляем таблицу...")
            self.load_assets_data()

    def issue_asset(self):
        """Выдача актива сотруднику"""
        print("📤 Открытие диалога выдачи актива...")
        dialog = IssueDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_assets_data()

    def return_asset(self):
        """Возврат актива"""
        print("📥 Открытие диалога возврата актива...")
        dialog = ReturnDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_assets_data()


def main():
    print("🎯 Запуск приложения...")
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    print("✅ Приложение запущено успешно")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

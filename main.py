import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTableView, QVBoxLayout,
                             QWidget, QPushButton, QMessageBox, QHBoxLayout, QDialog)  # ← ДОБАВИЛИ QDialog
from PyQt6.QtSql import QSqlDatabase, QSqlQueryModel
from PyQt6.QtCore import Qt

# Импортируем наш новый диалог
from views.asset_dialog import AssetDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_data()

    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        self.setWindowTitle("Система учета инструментов и расходников - АО КОНСИСТ-ОС")
        self.setGeometry(100, 100, 1200, 700)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Основной layout
        layout = QVBoxLayout(central_widget)

        # Панель кнопок
        buttons_layout = QHBoxLayout()

        # Кнопки управления
        self.btn_add = QPushButton("➕ Добавить актив")
        self.btn_edit = QPushButton("✏️ Редактировать")
        self.btn_delete = QPushButton("🗑️ Удалить")
        self.btn_refresh = QPushButton("🔄 Обновить")
        self.btn_issue = QPushButton("📤 Выдать")
        self.btn_return = QPushButton("📥 Вернуть")

        buttons_layout.addWidget(self.btn_add)
        buttons_layout.addWidget(self.btn_edit)
        buttons_layout.addWidget(self.btn_delete)
        buttons_layout.addWidget(self.btn_refresh)
        buttons_layout.addWidget(self.btn_issue)
        buttons_layout.addWidget(self.btn_return)
        buttons_layout.addStretch()

        layout.addLayout(buttons_layout)

        # Таблица для отображения данных
        self.table_view = QTableView()
        layout.addWidget(self.table_view)

        # Подключаем кнопки к функциям
        self.btn_refresh.clicked.connect(self.load_data)
        self.btn_add.clicked.connect(self.add_asset)
        self.btn_issue.clicked.connect(self.issue_asset)
        self.btn_return.clicked.connect(self.return_asset)

    def load_data(self):
        """Загрузка данных в таблицу с JOIN для читаемых названий"""
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
        self.table_view.setModel(model)
        self.table_view.resizeColumnsToContents()

        print("Данные успешно загружены в таблицу!")

    def add_asset(self):
        """Добавление нового актива"""
        dialog = AssetDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:  # ← ТЕПЕРЬ ДОЛЖНО РАБОТАТЬ
            # Если пользователь нажал "Сохранить", обновляем таблицу
            self.load_data()
            QMessageBox.information(self, "Успех", "Новый актив успешно добавлен в систему!")

    def issue_asset(self):
        """Выдача актива сотруднику"""
        QMessageBox.information(self, "Информация", "Функция выдачи актива будет реализована в следующем шаге!")

    def return_asset(self):
        """Возврат актива"""
        QMessageBox.information(self, "Информация", "Функция возврата актива будет реализована в следующем шаге!")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
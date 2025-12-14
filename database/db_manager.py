import sqlite3
import os
import sys
from PyQt6.QtCore import QMutex, QMutexLocker


class DatabaseManager:
    _instance = None
    _mutex = QMutex()

    def __new__(cls):
        with QMutexLocker(cls._mutex):
            if cls._instance is None:
                cls._instance = super(DatabaseManager, cls).__new__(cls)
                cls._instance._init_db()
            return cls._instance

    def _get_db_path(self):
        """Получить путь к БД в зависимости от режима запуска"""
        if getattr(sys, 'frozen', False):
            # Приложение запущено как bundle/exe
            if sys.platform == 'darwin':
                # macOS: сохраняем БД в Application Support
                app_data = os.path.expanduser('~/Library/Application Support/InstrumentTracker')
            elif sys.platform == 'win32':
                # Windows: сохраняем БД в AppData/Roaming
                app_data = os.path.join(os.environ.get('APPDATA', ''), 'InstrumentTracker')
            else:
                # Linux: сохраняем в ~/.local/share
                app_data = os.path.expanduser('~/.local/share/InstrumentTracker')
            
            os.makedirs(app_data, exist_ok=True)
            db_path = os.path.join(app_data, 'inventory.db')
            
            # Копируем начальную БД если её нет
            if not os.path.exists(db_path):
                bundle_db = os.path.join(sys._MEIPASS, 'inventory.db')
                if os.path.exists(bundle_db):
                    import shutil
                    shutil.copy2(bundle_db, db_path)
                    print(f"📋 Скопирована БД из bundle: {db_path}")
                else:
                    print(f"📋 БД в bundle не найдена, будет создана новая: {db_path}")
            return db_path
        else:
            # Разработка: в текущей директории
            return 'inventory.db'

    def _init_db(self):
        """Инициализация базы данных"""
        print("Инициализация базы данных...")

        # НЕ удаляем базу данных! Сохраняем данные между запусками
        db_path = self._get_db_path()
        db_exists = os.path.exists(db_path)
        
        print(f"📁 Путь к БД: {db_path}")

        self.connection = sqlite3.connect(db_path, check_same_thread=False)
        self.connection.execute("PRAGMA journal_mode=WAL")

        self._create_tables()

        # Проверяем, есть ли данные в БД (проверяем таблицу Employees)
        cursor = self.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM Employees")
        has_data = cursor.fetchone()[0] > 0

        # Заполняем тестовыми данными если база новая или пустая
        if not db_exists or not has_data:
            self._populate_test_data()
            print(" Новая база данных создана с тестовыми данными")
        else:
            print(" Подключение к существующей базе данных")

    def _create_tables(self):
        """Создание таблиц (если они не существуют)"""
        cursor = self.connection.cursor()

        # Таблица должностей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Positions (
                position_id INTEGER PRIMARY KEY AUTOINCREMENT,
                position_name VARCHAR(100) NOT NULL UNIQUE
            )
        ''')

        # Таблица сотрудников
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Employees (
                employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
                last_name VARCHAR(100) NOT NULL,
                first_name VARCHAR(100) NOT NULL,
                patronymic VARCHAR(100),
                position_id INTEGER,
                phone VARCHAR(20),
                email VARCHAR(100),
                FOREIGN KEY (position_id) REFERENCES Positions(position_id)
            )
        ''')

        # Таблица типов активов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Asset_Types (
                type_id INTEGER PRIMARY KEY AUTOINCREMENT,
                type_name VARCHAR(50) NOT NULL UNIQUE
            )
        ''')

        # Таблица местоположений
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Locations (
                location_id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_name VARCHAR(100) NOT NULL UNIQUE,
                is_custom BOOLEAN DEFAULT 0
            )
        ''')

        # Таблица активов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Assets (
                asset_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(200) NOT NULL,
                type_id INTEGER NOT NULL,
                model VARCHAR(100) NOT NULL,
                serial_number VARCHAR(100),
                current_status VARCHAR(20) DEFAULT 'Доступен',
                location_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1,
                FOREIGN KEY (type_id) REFERENCES Asset_Types(type_id),
                FOREIGN KEY (location_id) REFERENCES Locations(location_id)
            )
        ''')

        # Таблица истории использования
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Usage_History (
                history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id INTEGER NOT NULL,
                employee_id INTEGER NOT NULL,
                operation_type VARCHAR(20) NOT NULL,
                operation_date DATETIME NOT NULL,
                planned_return_date DATE,
                actual_return_date DATE,
                notes TEXT,
                FOREIGN KEY (asset_id) REFERENCES Assets(asset_id),
                FOREIGN KEY (employee_id) REFERENCES Employees(employee_id)
            )
        ''')

        # Таблица учетных записей пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                employee_id INTEGER,
                role VARCHAR(20) DEFAULT 'user',
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES Employees(employee_id)
            )
        ''')

        # Таблица запросов на выдачу активов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Asset_Requests (
                request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id INTEGER NOT NULL,
                employee_id INTEGER NOT NULL,
                request_date DATETIME NOT NULL,
                planned_return_date DATE,
                notes TEXT,
                status VARCHAR(20) DEFAULT 'pending',
                approved_by INTEGER,
                approved_at DATETIME,
                FOREIGN KEY (asset_id) REFERENCES Assets(asset_id),
                FOREIGN KEY (employee_id) REFERENCES Employees(employee_id),
                FOREIGN KEY (approved_by) REFERENCES Users(user_id)
            )
        ''')

        self.connection.commit()

    def _populate_test_data(self):
        """Заполнение тестовыми данными (только для новой базы)"""
        print("Заполнение тестовыми данными...")
        cursor = self.connection.cursor()

        try:
            # Должности
            positions = [('Инженер',), ('Техник',), ('Кладовщик',), ('Мастер',)]
            cursor.executemany('INSERT OR IGNORE INTO Positions (position_name) VALUES (?)', positions)

            # Типы активов
            asset_types = [('Инструмент',), ('Расходник',), ('Измерительный прибор',), ('Электроинструмент',)]
            cursor.executemany('INSERT OR IGNORE INTO Asset_Types (type_name) VALUES (?)', asset_types)

            # Местоположения - стандартные без пометки custom
            locations = [
                ('Склад №1', 0),
                ('Цех №5', 0),
                ('Лаборатория', 0),
                ('Мастерская', 0)
            ]
            cursor.executemany('INSERT OR IGNORE INTO Locations (location_name, is_custom) VALUES (?, ?)', locations)

            # Сотрудники (только если их нет)
            cursor.execute("SELECT COUNT(*) FROM Employees")
            if cursor.fetchone()[0] == 0:
                employees = [
                    ('Иванов', 'Иван', 'Иванович', 1, '+79990000001', 'ivanov@company.ru'),
                    ('Петров', 'Петр', 'Петрович', 2, '+79990000002', 'petrov@company.ru'),
                    ('Сидорова', 'Мария', 'Сергеевна', 3, '+79990000003', 'sidorova@company.ru'),
                ]
                cursor.executemany('''
                    INSERT INTO Employees 
                    (last_name, first_name, patronymic, position_id, phone, email) 
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', employees)

            # Тестовые активы (только если их нет)
            cursor.execute("SELECT COUNT(*) FROM Assets")
            if cursor.fetchone()[0] == 0:
                assets = [
                    ('Шуруповерт Bosch', 1, 'GSR 120-LI', 'BOSCH12345', 'Доступен', 1, 1),
                    ('Мультиметр', 3, 'DT-832', 'DT83267890', 'Доступен', 2, 1),
                    ('Перчатки защитные', 2, 'Premium', None, 'Доступен', 1, 10),
                    ('Молоток', 1, 'Профессиональный', None, 'Доступен', 1, 2),
                ]
                cursor.executemany('''
                    INSERT INTO Assets 
                    (name, type_id, model, serial_number, current_status, location_id, quantity) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', assets)

            self.connection.commit()
            print(" Тестовые данные успешно добавлены")

        except Exception as e:
            print(f"❌ Ошибка при заполнении тестовыми данными: {e}")
            self.connection.rollback()

    def execute_query(self, query, params=()):
        """Выполнение запроса с возвратом результата"""
        with QMutexLocker(self._mutex):
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            result = cursor.fetchall()
            return result

    def execute_update(self, query, params=()):
        """Выполнение запроса на обновление"""
        with QMutexLocker(self._mutex):
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            self.connection.commit()
            return cursor.lastrowid

    def get_table_row_count(self, table_name):
        """Получение количества строк в таблице"""
        result = self.execute_query(f"SELECT COUNT(*) FROM {table_name}")
        return result[0][0] if result else 0
    
    def update_asset_status(self, asset_id):
        """
        Обновить статус актива на основе активных выдач
        
        Логика:
        - 'Выдан' - если есть хотя бы одна активная выдача (operation_type='выдача' AND actual_return_date IS NULL)
        - 'Доступен' - если нет активных выдач И quantity > 0
        
        Args:
            asset_id: ID актива для обновления статуса
        """
        with QMutexLocker(self._mutex):
            cursor = self.connection.cursor()
            
            # Проверяем наличие активных выдач
            cursor.execute("""
                SELECT COUNT(*) 
                FROM Usage_History 
                WHERE asset_id = ? 
                  AND operation_type = 'выдача' 
                  AND actual_return_date IS NULL
            """, (asset_id,))
            
            active_issues = cursor.fetchone()[0]
            
            # Получаем текущее количество
            cursor.execute("SELECT quantity FROM Assets WHERE asset_id = ?", (asset_id,))
            result = cursor.fetchone()
            
            if not result:
                return  # Актив не найден
            
            quantity = result[0]
            
            # Определяем правильный статус
            if active_issues > 0:
                new_status = 'Выдан'
            elif quantity > 0:
                new_status = 'Доступен'
            else:
                new_status = 'Доступен'  # Или можно оставить как есть
            
            # Обновляем статус
            cursor.execute(
                "UPDATE Assets SET current_status = ? WHERE asset_id = ?",
                (new_status, asset_id)
            )
            self.connection.commit()
            
            print(f"Статус актива {asset_id} обновлен: {new_status} (активных выдач: {active_issues}, кол-во: {quantity})")

    def close(self):
        """Закрытие соединения с базой данных"""
        if hasattr(self, 'connection') and self.connection:
            self.connection.close()
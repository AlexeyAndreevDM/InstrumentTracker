import sqlite3
import os
from datetime import datetime


class Database:
    def __init__(self, db_path="inventory.db"):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        """Создание соединения с базой данных"""
        return sqlite3.connect(self.db_path)

    def init_db(self):
        """Инициализация базы данных и создание таблиц"""
        conn = self.get_connection()
        cursor = conn.cursor()

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

        # Таблица местоположений - ДОБАВИЛИ ПОЛЕ is_custom
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Locations (
                location_id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_name VARCHAR(100) NOT NULL UNIQUE,
                is_custom BOOLEAN DEFAULT 0
            )
        ''')

        # Таблица активов (инструменты и расходники)
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

        # Наполняем справочники тестовыми данными
        self._populate_test_data(cursor)
        
        # Аннулируем все существующие учетные записи (удаляем их)
        cursor.execute("DELETE FROM Users")

        conn.commit()
        conn.close()
        print("База данных успешно инициализирована!")

    def _populate_test_data(self, cursor):
        """Заполнение тестовыми данными"""
        # Должности
        positions = [
            ('Инженер',),
            ('Техник',),
            ('Кладовщик',),
            ('Мастер',)
        ]
        cursor.executemany('INSERT OR IGNORE INTO Positions (position_name) VALUES (?)', positions)

        # Типы активов
        asset_types = [
            ('Инструмент',),
            ('Расходник',),
            ('Измерительный прибор',),
            ('Электроинструмент',)
        ]
        cursor.executemany('INSERT OR IGNORE INTO Asset_Types (type_name) VALUES (?)', asset_types)

        # Местоположения - стандартные без пометки custom
        locations = [
            ('Склад №1', 0),
            ('Цех №5', 0),
            ('Лаборатория', 0),
            ('Мастерская', 0)
        ]
        cursor.executemany('INSERT OR IGNORE INTO Locations (location_name, is_custom) VALUES (?, ?)', locations)

        # Сотрудники
        employees = [
            ('Иванов', 'Иван', 'Иванович', 1, '+79990000001', 'ivanov@company.ru'),
            ('Петров', 'Петр', 'Петрович', 2, '+79990000002', 'petrov@company.ru'),
            ('Сидорова', 'Мария', 'Сергеевна', 3, '+79990000003', 'sidorova@company.ru'),
        ]
        cursor.executemany('''
            INSERT OR IGNORE INTO Employees 
            (last_name, first_name, patronymic, position_id, phone, email) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', employees)

        # Тестовые активы
        assets = [
            ('Шуруповерт Bosch', 1, 'GSR 120-LI', 'BOSCH12345', 'Доступен', 1, 1),
            ('Мультиметр', 3, 'DT-832', 'DT83267890', 'Доступен', 2, 1),
            ('Перчатки защитные', 2, 'Premium', None, 'Доступен', 1, 10),
            ('Молоток', 1, 'Профессиональный', None, 'Доступен', 1, 2),
        ]
        cursor.executemany('''
            INSERT OR IGNORE INTO Assets 
            (name, type_id, model, serial_number, current_status, location_id, quantity) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', assets)

    def add_custom_location(self, location_name):
        """Добавление пользовательского местоположения"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Добавляем звездочку к названию и помечаем как кастомное
        custom_name = f"{location_name} *"

        try:
            cursor.execute(
                "INSERT INTO Locations (location_name, is_custom) VALUES (?, 1)",
                (custom_name,)
            )
            conn.commit()
            location_id = cursor.lastrowid
            conn.close()
            return location_id
        except sqlite3.IntegrityError:
            # Если такое имя уже существует, вернем его ID
            cursor.execute("SELECT location_id FROM Locations WHERE location_name = ?", (custom_name,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None
import sqlite3
import os


def check_database():
    print("Проверка базы данных...")

    if not os.path.exists('inventory.db'):
        print("❌ База данных 'inventory.db' не существует!")
        return False

    try:
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()

        # Проверяем существование таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        print("📊 Найденные таблицы:")
        for table in tables:
            print(f"  - {table[0]}")

        # Проверяем содержимое таблицы Assets
        cursor.execute("SELECT COUNT(*) FROM Assets")
        assets_count = cursor.fetchone()[0]
        print(f"📦 Количество активов: {assets_count}")

        # Проверяем содержимое таблицы Employees
        cursor.execute("SELECT COUNT(*) FROM Employees")
        employees_count = cursor.fetchone()[0]
        print(f"👥 Количество сотрудников: {employees_count}")

        # Показываем несколько активов
        if assets_count > 0:
            cursor.execute("SELECT asset_id, name, current_status FROM Assets LIMIT 5")
            assets = cursor.fetchall()
            print("📋 Примеры активов:")
            for asset in assets:
                print(f"  - ID: {asset[0]}, Название: {asset[1]}, Статус: {asset[2]}")

        conn.close()
        return True

    except sqlite3.Error as e:
        print(f"❌ Ошибка при проверке базы данных: {e}")
        return False


if __name__ == "__main__":
    check_database()
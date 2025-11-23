# reset_db.py
import os
from database.db_core import Database


def reset_database():
    # Удаляем старую базу данных
    if os.path.exists("inventory.db"):
        os.remove("inventory.db")
        print("Старая база данных удалена")

    # Создаем новую
    db = Database()
    print("Новая база данных создана")


if __name__ == "__main__":
    reset_database()
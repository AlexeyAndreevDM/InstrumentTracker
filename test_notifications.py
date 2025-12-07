#!/usr/bin/env python3
"""
Тестирование модуля уведомлений
"""
import sys
import os

# Устанавливаем переменную окружения для графического режима (попытаемся использовать offscreen)
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QDate, QTimer
from database.db_manager import DatabaseManager
from notification_manager import NotificationManager


def setup_test_data():
    """Подготовка тестовых данных для проверки уведомлений"""
    db = DatabaseManager()
    
    print("📋 Подготовка тестовых данных...")
    
    # Проверяем, есть ли уже данные
    assets = db.execute_query("SELECT COUNT(*) FROM Assets")
    if assets[0][0] == 0:
        print("✅ База данных уже содержит тестовые данные")
        return
    
    # Получаем ID сотрудника и актива для создания записей с разными сроками
    employees = db.execute_query("SELECT employee_id FROM Employees LIMIT 1")
    assets_list = db.execute_query("SELECT asset_id FROM Assets WHERE current_status = 'Доступен' LIMIT 3")
    
    if not employees or not assets_list:
        print("❌ Недостаточно данных в БД")
        return
    
    employee_id = employees[0][0]
    today = QDate.currentDate()
    
    # Создаем записи с разными сроками возврата
    test_cases = [
        ("Завтра истекает срок", today.addDays(1)),
        ("Сегодня истекает срок", today),
        ("Просрочено", today.addDays(-1)),
    ]
    
    for i, (description, return_date) in enumerate(test_cases):
        if i < len(assets_list):
            asset_id = assets_list[i][0]
            
            # Обновляем статус актива
            db.execute_update(
                "UPDATE Assets SET current_status = 'Выдан' WHERE asset_id = ?",
                (asset_id,)
            )
            
            # Добавляем запись в историю
            db.execute_update(
                """
                INSERT INTO Usage_History 
                (asset_id, employee_id, operation_type, operation_date, planned_return_date)
                VALUES (?, ?, 'выдача', ?, ?)
                """,
                (asset_id, employee_id, today.toString("yyyy-MM-dd"), return_date.toString("yyyy-MM-dd"))
            )
            
            print(f"  ✓ {description}: {return_date.toString('yyyy-MM-dd')}")
    
    print("✅ Тестовые данные созданы")


def test_notification_manager():
    """Тестирование менеджера уведомлений"""
    print("\n🧪 Тестирование модуля уведомлений...")
    
    app = QApplication(sys.argv)
    
    # Создаем фиктивное окно
    from PyQt6.QtWidgets import QMainWindow
    window = QMainWindow()
    window.setWindowTitle("Тест уведомлений")
    window.setGeometry(100, 100, 600, 400)
    
    # Инициализируем менеджер уведомлений
    notification_manager = NotificationManager(window)
    
    print("✓ NotificationManager инициализирован")
    
    # Запускаем проверку сроков
    notification_manager.start_checking(interval_ms=5000)  # Проверка каждые 5 секунд
    print("✓ Проверка сроков запущена")
    
    # Показываем окно
    window.show()
    
    # Таймер для закрытия приложения через 15 секунд
    def close_app():
        print("\n✅ Тестирование завершено")
        notification_manager.cleanup()
        app.quit()
    
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(close_app)
    timer.start(15000)
    
    print("ℹ️ Приложение будет закрыто через 15 секунд...")
    
    sys.exit(app.exec())


def check_overdue_assets():
    """Проверка просроченных активов"""
    print("\n📊 Информация о просроченных активах:")
    
    notification_manager = NotificationManager()
    overdue_assets = notification_manager.get_overdue_assets()
    
    if overdue_assets:
        print(f"Найдено {len(overdue_assets)} просроченных активов:\n")
        for asset_id, asset_name, employee_name, planned_date, days_overdue in overdue_assets:
            print(f"  • {asset_name} (ID: {asset_id})")
            print(f"    Сотрудник: {employee_name}")
            print(f"    Плановая дата возврата: {planned_date}")
            print(f"    Дней просрочки: {days_overdue}\n")
    else:
        print("✅ Нет просроченных активов\n")


if __name__ == "__main__":
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ МОДУЛЯ УВЕДОМЛЕНИЙ")
    print("=" * 60)
    
    # Подготавливаем данные
    setup_test_data()
    
    # Проверяем просроченные активы
    check_overdue_assets()
    
    # Запускаем тестирование UI
    print("\n🖥️ Запуск тестирования UI уведомлений...")
    print("Следите за всплывающими уведомлениями в верхнем правом углу экрана\n")
    
    try:
        test_notification_manager()
    except KeyboardInterrupt:
        print("\n⚠️ Тестирование прервано пользователем")

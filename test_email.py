"""
Тестовый скрипт для проверки email-уведомлений
"""

from email_notifier import EmailNotifier
from database.db_manager import DatabaseManager

def test_email_configuration():
    """Тест настройки и отправки тестового письма"""
    print("=== Тест Email-уведомлений ===\n")
    
    # Создаем экземпляр
    notifier = EmailNotifier()
    
    # Настройка (замените на реальные данные)
    sender_email = input("Введите email отправителя (AlexAndreev132@yandex.ru): ").strip()
    if not sender_email:
        sender_email = "AlexAndreev132@yandex.ru"
    
    sender_password = input("Введите пароль приложения: ").strip()
    
    if not sender_password:
        print("Ошибка: пароль не может быть пустым!")
        return False
    
    notifier.configure(sender_email, sender_password)
    
    # Тестовый email
    test_recipient = input("Введите тестовый email получателя (по умолчанию AlexAndreev132@yandex.ru): ").strip()
    if not test_recipient:
        test_recipient = "AlexAndreev132@yandex.ru"
    
    print(f"\nОтправка тестового письма на {test_recipient}...")
    
    # Отправляем тестовое уведомление
    success = notifier.send_deadline_warning(
        employee_email=test_recipient,
        employee_name="Иванов Иван Иванович",
        asset_name="Дрель BOSCH GSR 12V",
        deadline_date="2025-12-14",
        days_until=0  # Срок истекает сегодня
    )
    
    if success:
        print("✓ Тестовое письмо успешно отправлено!")
    else:
        print("✗ Ошибка при отправке письма")
    
    return success


def test_check_notifications():
    """Тест проверки реальных уведомлений из базы данных"""
    print("\n=== Тест проверки уведомлений из БД ===\n")
    
    # Создаем экземпляр
    notifier = EmailNotifier()
    
    # Настройка
    sender_email = input("Введите email отправителя: ").strip()
    sender_password = input("Введите пароль приложения: ").strip()
    
    notifier.configure(sender_email, sender_password)
    
    # Проверяем и отправляем реальные уведомления
    print("\nПроверка сроков возврата в базе данных...")
    sent_count = notifier.check_and_send_notifications()
    
    print(f"\nРезультат: отправлено {sent_count} уведомлений")


def show_pending_notifications():
    """Показать список сотрудников с истекающими сроками"""
    print("\n=== Список уведомлений для отправки ===\n")
    
    db = DatabaseManager()
    
    query = """
        SELECT 
            e.email,
            e.last_name || ' ' || e.first_name || ' ' || COALESCE(e.patronymic, '') as employee_name,
            a.name as asset_name,
            uh.planned_return_date,
            CAST((julianday(uh.planned_return_date) - julianday('now')) AS INTEGER) as days_until
        FROM Usage_History uh
        JOIN Assets a ON uh.asset_id = a.asset_id
        JOIN Employees e ON uh.employee_id = e.employee_id
        WHERE uh.operation_type = 'выдача'
            AND uh.actual_return_date IS NULL
            AND (
                DATE(uh.planned_return_date) = DATE('now', '+1 day')
                OR DATE(uh.planned_return_date) = DATE('now')
                OR DATE(uh.planned_return_date) < DATE('now')
            )
        ORDER BY uh.planned_return_date ASC
    """
    
    results = db.execute_query(query)
    
    if not results:
        print("Нет уведомлений для отправки")
        return
    
    print(f"Найдено уведомлений: {len(results)}\n")
    
    for i, row in enumerate(results, 1):
        email, employee_name, asset_name, deadline_date, days_until = row
        
        if days_until == 0:
            status = "СЕГОДНЯ"
        elif days_until == 1:
            status = "ЗАВТРА"
        elif days_until < 0:
            status = f"ПРОСРОЧКА {abs(days_until)} дн."
        else:
            status = f"Через {days_until} дн."
        
        print(f"{i}. {employee_name}")
        print(f"   Email: {email if email else 'НЕ УКАЗАН'}")
        print(f"   Инструмент: {asset_name}")
        print(f"   Срок: {deadline_date} ({status})")
        print()


def main():
    """Главное меню тестирования"""
    while True:
        print("\n" + "="*50)
        print("Тестирование Email-уведомлений")
        print("="*50)
        print("1. Показать список уведомлений")
        print("2. Отправить тестовое письмо")
        print("3. Проверить и отправить реальные уведомления")
        print("0. Выход")
        print("="*50)
        
        choice = input("\nВыберите действие: ").strip()
        
        if choice == '1':
            show_pending_notifications()
        elif choice == '2':
            test_email_configuration()
        elif choice == '3':
            test_check_notifications()
        elif choice == '0':
            print("Выход")
            break
        else:
            print("Неверный выбор")


if __name__ == '__main__':
    main()

"""
Тестовый скрипт для проверки правильности обновления статусов активов
"""

from database.db_manager import DatabaseManager

def test_asset_status():
    """Тест обновления статусов активов"""
    print("=== Тест обновления статусов активов ===\n")
    
    db = DatabaseManager()
    
    # Получаем все активы с их статусами
    assets = db.execute_query("""
        SELECT 
            a.asset_id,
            a.name,
            a.quantity,
            a.current_status,
            COUNT(uh.history_id) as active_issues
        FROM Assets a
        LEFT JOIN Usage_History uh ON a.asset_id = uh.asset_id 
            AND uh.operation_type = 'выдача' 
            AND uh.actual_return_date IS NULL
        GROUP BY a.asset_id
        ORDER BY a.asset_id
    """)
    
    print(f"Всего активов в БД: {len(assets)}\n")
    
    issues_found = []
    
    for asset_id, name, quantity, current_status, active_issues in assets:
        # Определяем правильный статус
        if active_issues > 0:
            correct_status = 'Выдан'
        elif quantity > 0:
            correct_status = 'Доступен'
        else:
            correct_status = 'Доступен'
        
        # Проверяем соответствие
        status_ok = current_status == correct_status
        
        print(f"[{'✓' if status_ok else '✗'}] ID: {asset_id} | {name}")
        print(f"    Текущий статус: {current_status}")
        print(f"    Правильный статус: {correct_status}")
        print(f"    Кол-во: {quantity} | Активных выдач: {active_issues}")
        
        if not status_ok:
            issues_found.append((asset_id, name, current_status, correct_status))
            print(f"    ⚠️ НЕСООТВЕТСТВИЕ!")
        
        print()
    
    if issues_found:
        print(f"\n{'='*60}")
        print(f"Найдено проблем: {len(issues_found)}")
        print('='*60)
        
        for asset_id, name, current, correct in issues_found:
            print(f"  {name} (ID: {asset_id})")
            print(f"    Сейчас: '{current}', должно быть: '{correct}'")
        
        print('\n' + '='*60)
        fix = input("\nИсправить статусы автоматически? (y/n): ").strip().lower()
        
        if fix == 'y':
            print("\nИсправление статусов...")
            for asset_id, name, _, _ in issues_found:
                db.update_asset_status(asset_id)
                print(f"  ✓ {name} (ID: {asset_id})")
            print("\n✓ Все статусы исправлены!")
        else:
            print("\nИсправление отменено")
    else:
        print("✓ Все статусы корректны!")


def show_issued_assets():
    """Показать все выданные активы"""
    print("\n=== Выданные активы (активные выдачи) ===\n")
    
    db = DatabaseManager()
    
    issued = db.execute_query("""
        SELECT 
            a.asset_id,
            a.name,
            a.current_status,
            e.last_name || ' ' || e.first_name as employee_name,
            uh.planned_return_date,
            DATE(uh.planned_return_date) as return_date,
            DATE('now') as today
        FROM Usage_History uh
        JOIN Assets a ON uh.asset_id = a.asset_id
        JOIN Employees e ON uh.employee_id = e.employee_id
        WHERE uh.operation_type = 'выдача'
            AND uh.actual_return_date IS NULL
        ORDER BY uh.planned_return_date
    """)
    
    if not issued:
        print("Нет активных выдач")
        return
    
    print(f"Всего активных выдач: {len(issued)}\n")
    
    for asset_id, name, status, employee, return_date, return_date_clean, today in issued:
        print(f"• {name} (ID: {asset_id})")
        print(f"  Статус в БД: {status}")
        print(f"  У сотрудника: {employee}")
        print(f"  Дата возврата: {return_date}")
        
        if return_date_clean < today:
            print(f"  🚨 ПРОСРОЧЕНО!")
        elif return_date_clean == today:
            print(f"  ⚠️ Возврат сегодня")
        
        print()


def main():
    """Главное меню"""
    while True:
        print("\n" + "="*60)
        print("Тестирование статусов активов")
        print("="*60)
        print("1. Проверить все статусы")
        print("2. Показать выданные активы")
        print("3. Исправить все статусы (пересчитать)")
        print("0. Выход")
        print("="*60)
        
        choice = input("\nВыберите действие: ").strip()
        
        if choice == '1':
            test_asset_status()
        elif choice == '2':
            show_issued_assets()
        elif choice == '3':
            db = DatabaseManager()
            assets = db.execute_query("SELECT asset_id, name FROM Assets")
            print(f"\nПересчет статусов для {len(assets)} активов...")
            for asset_id, name in assets:
                db.update_asset_status(asset_id)
                print(f"  ✓ {name} (ID: {asset_id})")
            print("\n✓ Все статусы пересчитаны!")
        elif choice == '0':
            print("Выход")
            break
        else:
            print("Неверный выбор")


if __name__ == '__main__':
    main()

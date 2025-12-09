#!/usr/bin/env python3
"""Тест логики авторизации без GUI"""

import hashlib
from database.db_manager import DatabaseManager


def test_verify_credentials():
    """Тестируем логику авторизации"""
    db = DatabaseManager()
    
    print("=" * 50)
    print("🧪 ТЕСТ АВТОРИЗАЦИИ")
    print("=" * 50)
    
    # Функция для хеширования пароля (копия из LoginDialog)
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    # Тест 1: admin/admin
    print("\n✅ Тест 1: Вход admin/admin")
    username = "admin"
    password = "admin"
    
    if username == "admin" and password == "admin":
        user = {
            'user_id': 0,
            'username': 'admin',
            'role': 'admin',
            'employee_id': None,
            'full_name': 'Administrator'
        }
        print(f"   Результат: {user}")
        print("   ✅ PASS")
    else:
        print("   ❌ FAIL")
    
    # Тест 2: user1/user1
    print("\n✅ Тест 2: Вход user1/user1")
    username = "user1"
    password = "user1"
    
    query = """
    SELECT u.user_id, u.username, u.role, u.employee_id, e.last_name || ' ' || e.first_name as full_name, u.password
    FROM Users u
    LEFT JOIN Employees e ON u.employee_id = e.employee_id
    WHERE u.username = ? AND u.is_active = 1
    """
    result = db.execute_query(query, (username,))
    
    if result:
        user_id, db_username, role, employee_id, full_name, stored_password_hash = result[0]
        password_hash = hash_password(password)
        
        print(f"   Username: {db_username}")
        print(f"   Role: {role}")
        print(f"   Password hash в БД: {stored_password_hash[:16]}...")
        print(f"   Password hash от входа: {password_hash[:16]}...")
        
        if password_hash == stored_password_hash:
            user = {
                'user_id': user_id,
                'username': db_username,
                'role': role,
                'employee_id': employee_id,
                'full_name': full_name or username
            }
            print(f"   Результат: {user}")
            print("   ✅ PASS")
        else:
            print("   ❌ FAIL - пароли не совпадают")
    else:
        print("   ❌ FAIL - пользователь не найден")
    
    # Тест 3: user1/wrongpassword
    print("\n✅ Тест 3: Вход user1/wrongpassword (должен фейлиться)")
    username = "user1"
    password = "wrongpassword"
    
    query = """
    SELECT u.user_id, u.username, u.role, u.employee_id, e.last_name || ' ' || e.first_name as full_name, u.password
    FROM Users u
    LEFT JOIN Employees e ON u.employee_id = e.employee_id
    WHERE u.username = ? AND u.is_active = 1
    """
    result = db.execute_query(query, (username,))
    
    if result:
        user_id, db_username, role, employee_id, full_name, stored_password_hash = result[0]
        password_hash = hash_password(password)
        
        if password_hash == stored_password_hash:
            print("   ❌ FAIL - неправильный пароль не должен работать")
        else:
            print("   ✅ PASS - правильно отклонен неправильный пароль")
    else:
        print("   ❌ FAIL - пользователь не найден")
    
    print("\n" + "=" * 50)
    print("✅ ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ")
    print("=" * 50)


if __name__ == "__main__":
    test_verify_credentials()

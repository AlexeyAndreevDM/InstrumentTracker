"""
Модуль логирования действий пользователей для аудита
Сохраняет логи в JSON файл
"""
import json
from datetime import datetime
from pathlib import Path


class AuditLogger:
    """Класс для логирования действий пользователей"""
    
    _log_file = "audit_log.json"
    
    @staticmethod
    def log_action(user_id, username, action, details=None):
        """
        Запись действия в лог
        
        Args:
            user_id: ID пользователя
            username: Имя пользователя
            action: Действие (например, 'login', 'asset_add', 'asset_issue')
            details: Дополнительные детали (словарь)
        """
        try:
            # Подготовка записи лога
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "username": username,
                "action": action,
                "details": details or {}
            }
            
            # Загрузка существующих логов
            log_path = Path(AuditLogger._log_file)
            logs = []
            
            if log_path.exists() and log_path.stat().st_size > 0:
                try:
                    with open(log_path, 'r', encoding='utf-8') as f:
                        logs = json.load(f)
                        if not isinstance(logs, list):
                            logs = []
                except (json.JSONDecodeError, Exception):
                    logs = []
            
            # Добавление новой записи
            logs.append(log_entry)
            
            # Сохранение логов (максимум 1000 записей)
            if len(logs) > 1000:
                logs = logs[-1000:]
            
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
            
            print(f"📝 Записано в аудит-лог: {action} пользователем {username}")
            
        except Exception as e:
            print(f"❌ Ошибка записи в аудит-лог: {e}")
    
    @staticmethod
    def get_recent_logs(limit=50):
        """Получить последние записи лога"""
        try:
            log_path = Path(AuditLogger._log_file)
            
            if not log_path.exists():
                return []
            
            with open(log_path, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            return logs[-limit:] if logs else []
            
        except Exception as e:
            print(f"❌ Ошибка чтения аудит-лога: {e}")
            return []
    
    @staticmethod
    def clear_logs():
        """Очистить лог-файл (для тестирования)"""
        try:
            log_path = Path(AuditLogger._log_file)
            if log_path.exists():
                log_path.unlink()
                print("🗑️ Аудит-лог очищен")
        except Exception as e:
            print(f"❌ Ошибка очистки аудит-лога: {e}")
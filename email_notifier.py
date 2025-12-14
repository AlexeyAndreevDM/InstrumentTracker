"""
Модуль email-уведомлений для InstrumentTracker
Отправляет предупреждения о сроках возврата инструментов
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from database.db_manager import DatabaseManager


class EmailNotifier:
    """Класс для отправки email-уведомлений о сроках возврата"""
    
    def __init__(self, smtp_server='smtp.yandex.ru', smtp_port=587, sender_email=None, sender_password=None):
        """
        Инициализация email-отправителя
        
        Args:
            smtp_server: SMTP-сервер (по умолчанию Yandex)
            smtp_port: Порт SMTP-сервера
            sender_email: Email отправителя
            sender_password: Пароль или app password
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.db = DatabaseManager()
        
        # Флаг включения отправки (можно отключить для тестирования)
        self.enabled = False
        
    def configure(self, sender_email, sender_password):
        """Настроить параметры отправителя"""
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.enabled = True if sender_email and sender_password else False
        
    def send_email(self, recipient_email, subject, html_body, plain_body=None):
        """
        Отправить email-сообщение
        
        Args:
            recipient_email: Email получателя
            subject: Тема письма
            html_body: HTML-содержимое письма
            plain_body: Текстовое содержимое (опционально)
        
        Returns:
            bool: True если отправка успешна, иначе False
        """
        if not self.enabled:
            print(f"Email-уведомления отключены. Сообщение не отправлено: {subject}")
            return False
            
        if not recipient_email or '@' not in recipient_email:
            print(f"Некорректный email получателя: {recipient_email}")
            return False
            
        try:
            # Создаем multipart сообщение
            msg = MIMEMultipart('alternative')
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject
            
            # Текстовая версия (если не указана, берем из HTML)
            if plain_body is None:
                plain_body = subject + "\n\n" + "Пожалуйста, откройте это письмо в почтовом клиенте с поддержкой HTML."
            
            # Добавляем обе версии
            part1 = MIMEText(plain_body, 'plain', 'utf-8')
            part2 = MIMEText(html_body, 'html', 'utf-8')
            
            msg.attach(part1)
            msg.attach(part2)
            
            # Отправка через SMTP
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Шифрование
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
                
            print(f"Email отправлен: {recipient_email} - {subject}")
            return True
            
        except Exception as e:
            print(f"Ошибка отправки email на {recipient_email}: {e}")
            return False
    
    def send_deadline_warning(self, employee_email, employee_name, asset_name, deadline_date, days_until):
        """
        Отправить предупреждение о приближающемся сроке возврата
        
        Args:
            employee_email: Email сотрудника
            employee_name: ФИО сотрудника
            asset_name: Название инструмента
            deadline_date: Дата планируемого возврата
            days_until: Дней до срока (0 = сегодня, -1 = просрочено на 1 день)
        """
        if days_until == 0:
            subject = f"⚠️ СЕГОДНЯ срок возврата: {asset_name}"
            warning_text = "СЕГОДНЯ истекает срок возврата"
            color = "#ff9800"  # Оранжевый
        elif days_until == 1:
            subject = f"⏰ ЗАВТРА срок возврата: {asset_name}"
            warning_text = "ЗАВТРА истекает срок возврата"
            color = "#ffc107"  # Желтый
        elif days_until < 0:
            subject = f"🚨 ПРОСРОЧКА {abs(days_until)} дн.: {asset_name}"
            warning_text = f"ПРОСРОЧКА {abs(days_until)} дней"
            color = "#f44336"  # Красный
        else:
            subject = f"Напоминание о возврате: {asset_name}"
            warning_text = f"Осталось {days_until} дней"
            color = "#2196f3"  # Синий
        
        # HTML-шаблон письма
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: {color};
                    color: white;
                    padding: 20px;
                    border-radius: 5px 5px 0 0;
                    text-align: center;
                }}
                .content {{
                    background-color: #f9f9f9;
                    padding: 20px;
                    border: 1px solid #ddd;
                    border-top: none;
                    border-radius: 0 0 5px 5px;
                }}
                .info-block {{
                    background-color: white;
                    padding: 15px;
                    margin: 15px 0;
                    border-left: 4px solid {color};
                    border-radius: 3px;
                }}
                .info-label {{
                    font-weight: bold;
                    color: #666;
                }}
                .footer {{
                    margin-top: 20px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    font-size: 12px;
                    color: #999;
                    text-align: center;
                }}
                .warning {{
                    background-color: {color};
                    color: white;
                    padding: 10px;
                    border-radius: 3px;
                    text-align: center;
                    font-weight: bold;
                    margin: 15px 0;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🔧 InstrumentTracker</h2>
                <p>Уведомление о возврате инструмента</p>
            </div>
            <div class="content">
                <p>Здравствуйте, <strong>{employee_name}</strong>!</p>
                
                <div class="warning">
                    {warning_text}
                </div>
                
                <div class="info-block">
                    <p><span class="info-label">Инструмент:</span> {asset_name}</p>
                    <p><span class="info-label">Плановая дата возврата:</span> {deadline_date}</p>
                    <p><span class="info-label">Текущая дата:</span> {datetime.now().strftime('%Y-%m-%d')}</p>
                </div>
                
                <p>Пожалуйста, верните инструмент в указанный срок или продлите срок пользования в системе InstrumentTracker.</p>
                
                <p style="color: #666; font-size: 14px;">
                    ℹ️ Если инструмент уже возвращен, это уведомление можно проигнорировать.
                </p>
            </div>
            <div class="footer">
                <p>Это автоматическое уведомление из системы InstrumentTracker</p>
                <p>Не отвечайте на это письмо</p>
            </div>
        </body>
        </html>
        """
        
        # Текстовая версия
        plain_body = f"""
InstrumentTracker - Уведомление о возврате инструмента

Здравствуйте, {employee_name}!

{warning_text}

Инструмент: {asset_name}
Плановая дата возврата: {deadline_date}
Текущая дата: {datetime.now().strftime('%Y-%m-%d')}

Пожалуйста, верните инструмент в указанный срок или продлите срок пользования в системе InstrumentTracker.

---
Это автоматическое уведомление из системы InstrumentTracker
        """
        
        return self.send_email(employee_email, subject, html_body, plain_body)
    
    def check_and_send_notifications(self):
        """
        Проверить сроки возврата и отправить уведомления
        Вызывается периодически (например, раз в час или раз в день)
        """
        if not self.enabled:
            print("Email-уведомления отключены")
            return
        
        try:
            # Запрос активов с истекающими сроками
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
                    AND e.email IS NOT NULL
                    AND e.email != ''
                    AND (
                        -- Завтра истекает
                        DATE(uh.planned_return_date) = DATE('now', '+1 day')
                        OR
                        -- Сегодня истекает
                        DATE(uh.planned_return_date) = DATE('now')
                        OR
                        -- Просрочено
                        DATE(uh.planned_return_date) < DATE('now')
                    )
                ORDER BY uh.planned_return_date ASC
            """
            
            results = self.db.execute_query(query)
            
            sent_count = 0
            for row in results:
                email, employee_name, asset_name, deadline_date, days_until = row
                
                # Очищаем лишние пробелы из ФИО
                employee_name = ' '.join(employee_name.split())
                
                success = self.send_deadline_warning(
                    email,
                    employee_name,
                    asset_name,
                    deadline_date,
                    days_until
                )
                
                if success:
                    sent_count += 1
            
            print(f"Email-уведомлений отправлено: {sent_count}")
            return sent_count
            
        except Exception as e:
            print(f"Ошибка при проверке и отправке email-уведомлений: {e}")
            return 0

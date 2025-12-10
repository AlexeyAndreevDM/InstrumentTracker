import hashlib
from datetime import datetime
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QComboBox, QMessageBox, QTabWidget, QWidget, QSpinBox, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal
from database.db_manager import DatabaseManager


class LoginDialog(QDialog):
    """Окно входа с авторизацией пользователя"""
    
    login_successful = pyqtSignal(dict)  # Сигнал при успешной авторизации
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseManager()
        self.setWindowTitle("Вход в систему учета активов")
        self.setFixedSize(550, 550)
        self.setModal(True)
        
        # Инициализируем атрибуты для полей (используются в сигналах)
        self.register_username_input = None
        self.register_password_input = None
        self.register_employee_combo = None
        
        self.init_ui()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout()
        
        # Заголовок
        title_label = QLabel("Система учета инструментов и расходников")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 20px;")
        layout.addWidget(title_label)
        
        # Вкладки для входа и регистрации
        self.tabs = QTabWidget()
        
        # Вкладка входа
        login_tab = QWidget()
        self.setup_login_tab(login_tab)
        self.tabs.addTab(login_tab, "🔑 Вход")
        
        # Вкладка регистрации нового пользователя
        register_tab = QWidget()
        self.setup_register_tab(register_tab)
        self.tabs.addTab(register_tab, "✍️ Новый пользователь")
        
        layout.addWidget(self.tabs)
        
        self.setLayout(layout)
    
    def setup_login_tab(self, tab):
        """Настройка вкладки входа"""
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Имя пользователя
        username_label = QLabel("👤 Имя пользователя:")
        username_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(username_label)
        
        self.login_username_input = QLineEdit()
        self.login_username_input.setPlaceholderText("Введите имя пользователя")
        self.login_username_input.setFixedHeight(32)
        layout.addWidget(self.login_username_input)
        
        # Пароль с чекбоксом для видимости
        password_layout = QHBoxLayout()
        password_label = QLabel("🔑 Пароль:")
        password_label.setStyleSheet("font-size: 12px;")
        password_layout.addWidget(password_label)
        password_layout.addStretch()
        layout.addLayout(password_layout)
        
        password_input_layout = QHBoxLayout()
        password_input_layout.setContentsMargins(0, 0, 0, 0)
        password_input_layout.setSpacing(5)
        
        self.login_password_input = QLineEdit()
        self.login_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_password_input.setPlaceholderText("Введите пароль")
        self.login_password_input.setFixedHeight(32)
        password_input_layout.addWidget(self.login_password_input)
        
        self.login_show_password_checkbox = QCheckBox("👁️")
        self.login_show_password_checkbox.setMaximumWidth(30)
        self.login_show_password_checkbox.stateChanged.connect(self.toggle_login_password)
        password_input_layout.addWidget(self.login_show_password_checkbox)
        
        layout.addLayout(password_input_layout)
        
        # Кнопка входа
        login_btn = QPushButton("🔓 Вход")
        login_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        login_btn.setFixedHeight(40)
        login_btn.clicked.connect(self.on_login_click)
        layout.addWidget(login_btn)
        
        layout.addStretch()
    
    def setup_register_tab(self, tab):
        """Настройка вкладки регистрации нового пользователя"""
        layout = QVBoxLayout(tab)
        layout.setSpacing(8)
        layout.setContentsMargins(30, 20, 30, 20)
        
        # ФИО из списка сотрудников
        employee_label = QLabel("👥 Выберите сотрудника или введите ФИО:")
        employee_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(employee_label)
        
        self.register_employee_combo = QComboBox()
        self.register_employee_combo.setEditable(True)
        self.register_employee_combo.setFixedHeight(30)
        self.register_employee_combo.setPlaceholderText("--Выберите сотрудника или введите ФИО--")
        self.register_employee_combo.currentIndexChanged.connect(self.on_employee_selected)
        self.register_employee_combo.editTextChanged.connect(self.on_employee_text_changed)
        
        # Загружаем сотрудников
        self.load_employees_to_combo()
        layout.addWidget(self.register_employee_combo)
        
        # Автозаполняемое имя пользователя
        username_label = QLabel("📝 Имя пользователя (автоматическое):")
        username_label.setStyleSheet("font-size: 12px; margin-top: 5px;")
        layout.addWidget(username_label)
        
        self.register_username_input = QLineEdit()
        self.register_username_input.setReadOnly(True)
        self.register_username_input.setFixedHeight(28)
        self.register_username_input.setStyleSheet("background-color: #f0f0f0; color: #000000;")
        layout.addWidget(self.register_username_input)
        
        # Пароль с чекбоксом для видимости
        password_layout = QHBoxLayout()
        password_label = QLabel("🔑 Пароль:")
        password_label.setStyleSheet("font-size: 12px;")
        password_layout.addWidget(password_label)
        password_layout.addStretch()
        layout.addLayout(password_layout)
        
        password_input_layout = QHBoxLayout()
        password_input_layout.setContentsMargins(0, 0, 0, 0)
        password_input_layout.setSpacing(5)
        
        self.register_password_input = QLineEdit()
        self.register_password_input.setReadOnly(True)
        self.register_password_input.setFixedHeight(28)
        self.register_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.register_password_input.setStyleSheet("background-color: #f0f0f0; color: #000000;")
        password_input_layout.addWidget(self.register_password_input)
        
        self.register_show_password_checkbox = QCheckBox("👁️")
        self.register_show_password_checkbox.setMaximumWidth(30)
        self.register_show_password_checkbox.stateChanged.connect(self.toggle_register_password)
        password_input_layout.addWidget(self.register_show_password_checkbox)
        
        layout.addLayout(password_input_layout)
        
        # Информационная подсказка
        info_label = QLabel("ℹ️ Автоматически: user1, user2 и т.д.")
        info_label.setStyleSheet("color: #666; font-size: 10px; margin-top: 3px;")
        layout.addWidget(info_label)
        
        # Кнопка создания аккаунта
        register_btn = QPushButton("✅ Создать аккаунт")
        register_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 8px;")
        register_btn.setFixedHeight(35)
        register_btn.clicked.connect(self.on_register_click)
        layout.addWidget(register_btn)
        
        layout.addStretch()
    
    def load_employees_to_combo(self):
        """Загрузка списка сотрудников"""
        try:
            # Получаем сотрудников, у которых еще нет аккаунта
            query = """
            SELECT e.employee_id, e.last_name || ' ' || e.first_name || ' ' || COALESCE(e.patronymic, '') as full_name
            FROM Employees e
            ORDER BY e.last_name, e.first_name
            """
            employees = self.db.execute_query(query)
            
            self.register_employee_combo.clear()
            self.register_employee_combo.addItem("-- Выберите сотрудника --", None)
            
            for emp_id, full_name in employees:
                self.register_employee_combo.addItem(full_name.strip(), emp_id)
        
        except Exception as e:
            print(f"Ошибка загрузки сотрудников: {e}")
    
    def on_employee_selected(self, index):
        """Обработчик выбора сотрудника из списка"""
        # Проверяем, инициализированы ли поля
        if self.register_username_input is None or self.register_password_input is None:
            return
        
        if self.register_employee_combo is None:
            return
        
        employee_id = self.register_employee_combo.currentData()
        
        if employee_id:
            # Получаем следующий номер пользователя
            next_user_num = self._get_next_user_number()
            username = f"user{next_user_num}"
            
            self.register_username_input.setText(username)
            self.register_password_input.setText(username)
        else:
            self.register_username_input.clear()
            self.register_password_input.clear()
    
    def on_employee_text_changed(self, text):
        """Обработчик изменения текста в editable combobox"""
        # Проверяем, инициализированы ли поля
        if self.register_username_input is None or self.register_password_input is None:
            return
        
        text = text.strip()
        if text and text != "--Выберите сотрудника или введите ФИО--":
            # Есть текст - генерируем username
            next_user_num = self._get_next_user_number()
            username = f"user{next_user_num}"
            
            self.register_username_input.setText(username)
            self.register_password_input.setText(username)
        else:
            self.register_username_input.clear()
            self.register_password_input.clear()
    
    def _get_next_user_number(self):
        """Получает следующий номер пользователя"""
        try:
            # Получаем максимальный номер user
            query = "SELECT MAX(CAST(SUBSTR(username, 5) AS INTEGER)) FROM Users WHERE username LIKE 'user%'"
            result = self.db.execute_query(query)
            
            if result and result[0][0]:
                return result[0][0] + 1
            return 1
        except:
            return 1
    
    def on_login_click(self):
        """Обработчик нажатия кнопки входа"""
        username = self.login_username_input.text().strip()
        password = self.login_password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Введите имя пользователя и пароль!")
            return
        
        # Проверяем учетные данные
        user = self._verify_credentials(username, password)
        
        if user:
            QMessageBox.information(self, "Успех", f"✅ Добро пожаловать, {username}!")
            self.login_successful.emit(user)
            self.accept()
        else:
            QMessageBox.critical(self, "Ошибка", "❌ Неверное имя пользователя или пароль!")
            self.login_password_input.clear()
    
    def on_register_click(self):
        """Обработчик регистрации нового пользователя"""
        employee_id = self.register_employee_combo.currentData()
        employee_text = self.register_employee_combo.currentText().strip()
        username = self.register_username_input.text().strip()
        password = self.register_password_input.text()
        
        # Если нет выбранного employee_id, но есть текст - это новый сотрудник
        if not employee_id and not employee_text:
            QMessageBox.warning(self, "Ошибка", "Выберите сотрудника или введите ФИО!")
            return
        
        # Если employee_id не выбран, но есть текст - создаём нового сотрудника
        if not employee_id and employee_text:
            try:
                # Разбираем ФИО: может быть "Иванов Иван", "Иванов Иван Иванович", или просто "Иван Иванович"
                parts = employee_text.split()
                last_name = parts[0] if len(parts) > 0 else ""
                first_name = parts[1] if len(parts) > 1 else ""
                patronymic = parts[2] if len(parts) > 2 else None
                
                # Вставляем нового сотрудника
                query = "INSERT INTO Employees (last_name, first_name, patronymic) VALUES (?, ?, ?)"
                employee_id = self.db.execute_update(query, (last_name, first_name, patronymic))
                print(f"✅ Создан новый сотрудник: {employee_text} (ID: {employee_id})")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при создании сотрудника:\n{str(e)}")
                return
        
        # Проверяем, существует ли уже аккаунт для этого сотрудника
        query = "SELECT user_id FROM Users WHERE employee_id = ?"
        existing = self.db.execute_query(query, (employee_id,))
        
        if existing:
            emp_name = self.register_employee_combo.currentText()
            QMessageBox.warning(self, "Ошибка", f"Для сотрудника '{emp_name}' уже создан аккаунт!\n\nОдин сотрудник - один аккаунт.")
            return
        
        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Имя пользователя и пароль не могут быть пустыми!")
            return
        
        # Проверяем, существует ли уже такой username (на случай, если кто-то вручную меняет)
        query = "SELECT user_id FROM Users WHERE username = ?"
        existing = self.db.execute_query(query, (username,))
        
        if existing:
            QMessageBox.warning(self, "Ошибка", f"Пользователь {username} уже существует!")
            return
        
        try:
            # Создаем пароль (хешируем)
            password_hash = self._hash_password(password)
            
            # Добавляем пользователя в БД
            query = """
            INSERT INTO Users (username, password, employee_id, role, created_at)
            VALUES (?, ?, ?, ?, ?)
            """
            user_id = self.db.execute_update(
                query,
                (username, password_hash, employee_id, 'user', datetime.now().isoformat())
            )
            
            QMessageBox.information(
                self, 
                "Успех", 
                f"✅ Аккаунт '{username}' успешно создан!\n\nТеперь вы можете войти с этими данными."
            )
            
            # Переходим на вкладку входа
            self.tabs.setCurrentIndex(0)
            self.login_username_input.setText(username)
            self.login_password_input.setFocus()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании аккаунта:\n{str(e)}")
    
    def _verify_credentials(self, username, password):
        """Проверка учетных данных"""
        try:
            # Специальный случай: admin/admin - всегда доступен
            if username == "admin" and password == "admin":
                return {
                    'user_id': 0,
                    'username': 'admin',
                    'role': 'admin',
                    'employee_id': None,
                    'full_name': 'Administrator'
                }
            
            # Для обычных пользователей ищем в БД
            query = """
            SELECT u.user_id, u.username, u.role, u.employee_id, e.last_name || ' ' || e.first_name as full_name, u.password
            FROM Users u
            LEFT JOIN Employees e ON u.employee_id = e.employee_id
            WHERE u.username = ? AND u.is_active = 1
            """
            result = self.db.execute_query(query, (username,))
            
            if not result:
                return None
            
            user_id, db_username, role, employee_id, full_name, stored_password_hash = result[0]
            
            # Проверяем пароль
            password_hash = self._hash_password(password)
            if password_hash != stored_password_hash:
                return None
            
            return {
                'user_id': user_id,
                'username': db_username,
                'role': role,
                'employee_id': employee_id,
                'full_name': full_name or username
            }
        
        except Exception as e:
            print(f"Ошибка при проверке учетных данных: {e}")
            return None
    
    def toggle_login_password(self, state):
        """Переключение видимости пароля на вкладке входа"""
        if state:
            self.login_password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.login_password_input.setEchoMode(QLineEdit.EchoMode.Password)
    
    def toggle_register_password(self, state):
        """Переключение видимости пароля на вкладке регистрации"""
        if state:
            self.register_password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.register_password_input.setEchoMode(QLineEdit.EchoMode.Password)
    
    @staticmethod
    def _hash_password(password):
        """Хеширование пароля"""
        return hashlib.sha256(password.encode()).hexdigest()

"""Theme manager for dark/light themes"""
from PyQt6.QtCore import QSettings


class ThemeManager:
    """Управление темами приложения"""
    
    # Тёмная тема
    DARK_THEME = {
        'name': 'dark',
        'display_name': '🌙 Тёмная тема',
        'app_stylesheet': """
            QMainWindow {
                background-color: #1e1e1e;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QMenuBar {
                background-color: #2e2e2e;
                color: #ffffff;
                border-bottom: 1px solid #3e3e3e;
            }
            QMenuBar::item:selected {
                background-color: #3e3e3e;
            }
            QMenu {
                background-color: #2e2e2e;
                color: #ffffff;
                border: 1px solid #3e3e3e;
            }
            QMenu::item:selected {
                background-color: #3e3e3e;
            }
            QTabWidget::pane {
                border: 1px solid #3e3e3e;
            }
            QTabBar::tab {
                background-color: #2e2e2e;
                color: #ffffff;
                padding: 8px 20px;
                border: 1px solid #3e3e3e;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #3e3e3e;
                border-bottom: 2px solid #0d47a1;
            }
            QTableView {
                background-color: #2e2e2e;
                color: #ffffff;
                gridline-color: #3e3e3e;
                border: 1px solid #3e3e3e;
            }
            QTableView::item:selected {
                background-color: #0d47a1;
            }
            QHeaderView::section {
                background-color: #2e2e2e;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #3e3e3e;
            }
            QPushButton {
                background-color: #0d47a1;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:pressed {
                background-color: #0a3d91;
            }
            QPushButton:disabled {
                background-color: #3e3e3e;
                color: #666666;
            }
            QLineEdit {
                background-color: #2e2e2e;
                color: #ffffff;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
                padding: 5px;
            }
            QLineEdit:focus {
                border: 2px solid #0d47a1;
            }
            QComboBox {
                background-color: #2e2e2e;
                color: #ffffff;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
                padding: 5px;
            }
            QComboBox:focus {
                border: 2px solid #0d47a1;
            }
            QComboBox::drop-down {
                background-color: #2e2e2e;
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #2e2e2e;
                color: #ffffff;
                selection-background-color: #0d47a1;
            }
            QDateEdit {
                background-color: #2e2e2e;
                color: #ffffff;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
                padding: 5px;
            }
            QDateEdit:focus {
                border: 2px solid #0d47a1;
            }
            QSpinBox {
                background-color: #2e2e2e;
                color: #ffffff;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
                padding: 5px;
            }
            QCheckBox {
                color: #ffffff;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #2e2e2e;
                border: 1px solid #3e3e3e;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #0d47a1;
                border: 1px solid #0d47a1;
                border-radius: 3px;
                image: url(:/checked);
            }
            QLabel {
                color: #ffffff;
            }
            QGroupBox {
                color: #ffffff;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
                padding: 10px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
            QTextEdit {
                background-color: #2e2e2e;
                color: #ffffff;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
                padding: 5px;
            }
            QScrollBar:vertical {
                background-color: #1e1e1e;
                width: 12px;
                border: 1px solid #3e3e3e;
            }
            QScrollBar::handle:vertical {
                background-color: #555555;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #666666;
            }
            QScrollBar:horizontal {
                background-color: #1e1e1e;
                height: 12px;
                border: 1px solid #3e3e3e;
            }
            QScrollBar::handle:horizontal {
                background-color: #555555;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #666666;
            }
        """,
        'user_info_style': "padding: 10px; background-color: #0d47a1; color: #ffffff; font-weight: bold; border-radius: 5px;",
    }
    
    # Светлая тема
    LIGHT_THEME = {
        'name': 'light',
        'display_name': '☀️ Светлая тема',
        'app_stylesheet': """
            QMainWindow {
                background-color: #ffffff;
            }
            QWidget {
                background-color: #ffffff;
                color: #000000;
            }
            QMenuBar {
                background-color: #f5f5f5;
                color: #000000;
                border-bottom: 1px solid #e0e0e0;
            }
            QMenuBar::item:selected {
                background-color: #e0e0e0;
            }
            QMenu {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #e0e0e0;
            }
            QMenu::item:selected {
                background-color: #e3f2fd;
            }
            QTabWidget::pane {
                border: 1px solid #e0e0e0;
            }
            QTabBar::tab {
                background-color: #f5f5f5;
                color: #000000;
                padding: 8px 20px;
                border: 1px solid #e0e0e0;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                border-bottom: 2px solid #1976d2;
            }
            QTableView {
                background-color: #ffffff;
                color: #000000;
                gridline-color: #e0e0e0;
                border: 1px solid #e0e0e0;
            }
            QTableView::item:selected {
                background-color: #bbdefb;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                color: #000000;
                padding: 5px;
                border: 1px solid #e0e0e0;
            }
            QPushButton {
                background-color: #1976d2;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
            QPushButton:disabled {
                background-color: #e0e0e0;
                color: #999999;
            }
            QLineEdit {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #bdbdbd;
                border-radius: 4px;
                padding: 5px;
            }
            QLineEdit:focus {
                border: 2px solid #1976d2;
            }
            QComboBox {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #bdbdbd;
                border-radius: 4px;
                padding: 5px;
            }
            QComboBox:focus {
                border: 2px solid #1976d2;
            }
            QComboBox::drop-down {
                background-color: #ffffff;
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #000000;
                selection-background-color: #bbdefb;
            }
            QDateEdit {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #bdbdbd;
                border-radius: 4px;
                padding: 5px;
            }
            QDateEdit:focus {
                border: 2px solid #1976d2;
            }
            QSpinBox {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #bdbdbd;
                border-radius: 4px;
                padding: 5px;
            }
            QCheckBox {
                color: #000000;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #ffffff;
                border: 1px solid #bdbdbd;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #1976d2;
                border: 1px solid #1976d2;
                border-radius: 3px;
                image: url(:/checked);
            }
            QLabel {
                color: #000000;
            }
            QGroupBox {
                color: #000000;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 10px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
            QTextEdit {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #bdbdbd;
                border-radius: 4px;
                padding: 5px;
            }
            QScrollBar:vertical {
                background-color: #f5f5f5;
                width: 12px;
                border: 1px solid #e0e0e0;
            }
            QScrollBar::handle:vertical {
                background-color: #bbbbbb;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #ababab;
            }
            QScrollBar:horizontal {
                background-color: #f5f5f5;
                height: 12px;
                border: 1px solid #e0e0e0;
            }
            QScrollBar::handle:horizontal {
                background-color: #bbbbbb;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #ababab;
            }
        """,
        'user_info_style': "padding: 10px; background-color: #e3f2fd; color: #1976d2; font-weight: bold; border-radius: 5px;",
    }
    
    THEMES = {
        'dark': DARK_THEME,
        'light': LIGHT_THEME,
    }
    
    @staticmethod
    def get_theme(theme_name='dark'):
        """Получить тему по названию"""
        return ThemeManager.THEMES.get(theme_name, ThemeManager.DARK_THEME)
    
    @staticmethod
    def get_all_themes():
        """Получить все доступные темы"""
        return list(ThemeManager.THEMES.keys())
    
    @staticmethod
    def save_theme(theme_name):
        """Сохранить выбранную тему в настройки"""
        settings = QSettings('KONSIST-OS', 'InstrumentTracker')
        settings.setValue('theme', theme_name)
    
    @staticmethod
    def load_theme():
        """Загрузить сохранённую тему из настроек"""
        settings = QSettings('KONSIST-OS', 'InstrumentTracker')
        theme = settings.value('theme', 'dark')  # По умолчанию тёмная
        return theme

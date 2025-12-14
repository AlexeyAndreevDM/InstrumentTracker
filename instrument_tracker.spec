# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],  # Главный файл
    pathex=[],  # Пути для поиска модулей
    binaries=[],  # Внешние бинарные файлы (если есть)
    datas=[
        ('pictures/InstrumentTracker_icon.png', '.'),  # Иконка приложения
        ('pictures/InstrumentTracker_logo.png', '.'),  # Логотип
        # Если у вас есть другие ресурсы, добавьте их здесь
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtSql',
        'openpyxl',
        'sqlite3',
        # Дополнительные скрытые импорты
    ],
    hookspath=[],  # Пути к хукам
    hooksconfig={},  # Конфигурация хуков
    runtime_hooks=[],  # Runtime хуки
    excludes=[],  # Модули для исключения
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Исключаем ненужные модули для уменьшения размера
a.excludes.extend([
    'matplotlib', 'scipy', 'numpy',  # Если не используете
    'PIL', 'tkinter',  # Если не используете
])

# Добавляем путь к иконке для EXE
icon_path = 'InstrumentTracker_icon.png'

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='InstrumentTracker',  # Имя EXE файла
    debug=False,  # Отладка
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Сжатие UPX (установите отдельно)
    upx_exclude=[],  # Исключения для UPX
    runtime_tmpdir=None,
    console=False,  # Без консоли (GUI приложение)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,  # Путь к иконке
)
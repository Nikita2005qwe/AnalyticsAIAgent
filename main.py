"""
Точка входа в программу: AI-агент для помощи Аналитику

Задача:
    - Создать экземпляр Application
    - Запустить GUI
"""

from src.core.application import Application


def main():
    """Запуск приложения."""
    app = Application()
    app.run()


if __name__ == "__main__":
    main()
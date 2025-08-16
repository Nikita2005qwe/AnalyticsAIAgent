# main.py
import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QMessageBox
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QTimer, QUrl


class TasksPlanner(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Планировщик задач")
        self.setGeometry(100, 100, 1200, 800)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Веб-просмотр
        self.web_view = QWebEngineView()
        self.load_page()

        # Кнопки управления
        self.reload_button = QPushButton("🔄 Перезагрузить")
        self.clear_button = QPushButton("🗑️ Очистить все задачи")

        # Стилизация кнопок
        self.reload_button.setStyleSheet("background-color: #007BFF; color: white; font-size: 14px;")
        self.clear_button.setStyleSheet("background-color: #f44336; color: white; font-size: 14px;")

        self.reload_button.clicked.connect(self.load_page)
        self.clear_button.clicked.connect(self.clear_all_tasks)

        # Добавляем кнопки в макет
        button_layout = QVBoxLayout()
        button_layout.addWidget(self.reload_button)
        button_layout.addWidget(self.clear_button)

        self.main_layout.addWidget(self.web_view)
        # Добавляем кнопки как группу
        buttons_widget = QWidget()
        buttons_widget.setLayout(button_layout)
        self.main_layout.addWidget(buttons_widget)

        # Таймер проверки времени (каждую минуту)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_task_completion)
        self.timer.start(60000)  # Каждую минуту

    def load_page(self):
        """Загружает HTML по file:// URL"""
        html_path = os.path.abspath("index.html")
        if not os.path.exists(html_path):
            QMessageBox.critical(self, "Ошибка", "Файл index.html не найден!")
            sys.exit(1)
        url = QUrl.fromLocalFile(html_path)
        self.web_view.load(url)

    def clear_all_tasks(self):
        """Очистка всех задач"""
        reply = QMessageBox.question(
            self, 'Подтверждение очистки',
            'Вы уверены, что хотите удалить ВСЕ задачи?\nЭто действие нельзя отменить!',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.web_view.page().runJavaScript("""
                tasks = [];
                localStorage.setItem('tasks', JSON.stringify(tasks));
                renderTasks();
            """)
            QMessageBox.information(self, 'Готово', 'Все задачи удалены!')

    def check_task_completion(self):
        """Проверка задач (только для уведомлений, не изменяет статус)"""
        self.web_view.page().runJavaScript("""
            if (typeof tasks !== 'undefined') {
                let hasOverdue = false;
                tasks.forEach(task => {
                    if (!task.completed) {
                        const [h, m] = task.startTime.split(':').map(Number);
                        const duration = parseInt(task.duration);
                        const start = new Date();
                        start.setHours(h, m, 0, 0);
                        const end = new Date(start.getTime() + duration * 60000);
                        const now = new Date();

                        if (now >= end) {
                            hasOverdue = true;
                        }
                    }
                });

                if (hasOverdue) {
                    console.log("Есть просроченные задачи!");
                }
            }
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TasksPlanner()
    window.show()
    sys.exit(app.exec_())
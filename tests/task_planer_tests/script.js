<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no, maximum-scale=1.0, minimum-scale=1.0">
    <title>Планировщик задач</title>
    <style>
        /* Фиксированный масштаб 150% */
        html {
            zoom: 1.5;
            -moz-transform: scale(1.5);
            -moz-transform-origin: 0 0;
        }

        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f4f4f4;
            overflow: hidden; /* Запрет прокрутки */
        }

        /* Виджет времени */
        #time-widget {
            position: fixed;
            top: 10px;
            right: 10px;
            background-color: #2196F3;
            color: white;
            padding: 10px 15px;
            border-radius: 8px;
            font-size: 18px;
            font-weight: bold;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            z-index: 1000;
        }

        h1, h2 {
            text-align: center;
        }

        form {
            max-width: 600px;
            margin: 20px auto;
            padding: 20px;
            background-color: #fff;
            border: 1px solid #ddd;
            border-radius: 8px;
        }

        form label {
            display: block;
            margin-bottom: 5px;
        }

        form input, form textarea, form select {
            width: 100%;
            padding: 8px;
            margin-bottom: 15px;
            border: 1px solid #ccc;
            border-radius: 4px;
        }

        form button {
            padding: 10px 20px;
            background-color: #007BFF;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }

        form button:hover {
            background-color: #0056b3;
        }

        table {
            width: 100%;
            margin-top: 20px;
            border-collapse: collapse;
        }

        table th, table td {
            padding: 10px;
            text-align: left;
            border: 1px solid #ddd;
        }

        table th {
            background-color: #f2f2f2;
        }

        .priority-low {
            background-color: lightgreen;
        }

        .priority-medium {
            background-color: lightyellow;
        }

        .priority-high {
            background-color: lightsalmon;
        }

        /* Статусы задач */
        .status-active {
            background-color: #ffeb3b; /* Жёлтый - активная */
        }

        .status-overdue {
            background-color: #f44336; /* Красный - просрочена */
            color: white;
        }

        .section {
            margin-top: 20px;
            background-color: #fff;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 8px;
        }

        /* Запрет выделения текста */
        body {
            -webkit-user-select: none;
            -moz-user-select: none;
            -ms-user-select: none;
            user-select: none;
        }
    </style>
</head>
<body>
    <!-- Виджет текущего времени -->
    <div id="time-widget">00:00:00</div>

    <h1>Планировщик задач</h1>

    <form id="taskForm">
        <label for="taskName">Название задачи:</label>
        <input type="text" id="taskName" required>

        <label for="taskDescription">Описание:</label>
        <textarea id="taskDescription" rows="3"></textarea>

        <label for="startTime">Время начала:</label>
        <input type="time" id="startTime" required>

        <label for="duration">Длительность (минут):</label>
        <input type="number" id="duration" min="1" required>

        <label for="priority">Приоритет:</label>
        <select id="priority">
            <option value="low">Низкий</option>
            <option value="medium">Средний</option>
            <option value="high">Высокий</option>
        </select>

        <button type="submit">Добавить задачу</button>
    </form>

    <div class="section">
        <h2>Основные задачи</h2>
        <table id="mainTasksTable">
            <thead>
                <tr>
                    <th>Название</th>
                    <th>Описание</th>
                    <th>Время начала</th>
                    <th>Длительность</th>
                    <th>Время окончания</th>
                    <th>Приоритет</th>
                    <th>Статус</th>
                    <th>Действия</th>
                </tr>
            </thead>
            <tbody></tbody>
        </table>
    </div>

    <div class="section">
        <h2>Выполненные задачи</h2>
        <table id="completedTasksTable">
            <thead>
                <tr>
                    <th>Название</th>
                    <th>Описание</th>
                    <th>Время начала</th>
                    <th>Длительность</th>
                    <th>Время окончания</th>
                    <th>Приоритет</th>
                    <th>Статус</th>
                </tr>
            </thead>
            <tbody></tbody>
        </table>
    </div>

    <script>
        // Инициализация задач
        let tasks = JSON.parse(localStorage.getItem('tasks')) || [];

        // Обновление виджета времени
        function updateTimeWidget() {
            const now = new Date();
            const timeString = now.toLocaleTimeString('ru-RU', { 
                hour: '2-digit', 
                minute: '2-digit', 
                second: '2-digit' 
            });
            document.getElementById('time-widget').textContent = timeString;
        }

        // Обновляем время каждую секунду
        setInterval(updateTimeWidget, 1000);
        updateTimeWidget(); // Инициализация сразу

        function saveTasks() {
            localStorage.setItem('tasks', JSON.stringify(tasks));
        }

        // Функция для вычисления времени окончания
        function calculateEndTime(startTime, duration) {
            const [hours, minutes] = startTime.split(':').map(Number);
            const start = new Date();
            start.setHours(hours, minutes, 0, 0);
            const end = new Date(start.getTime() + duration * 60000);
            return `${end.getHours().toString().padStart(2, '0')}:${end.getMinutes().toString().padStart(2, '0')}`;
        }

        // Функция для определения статуса задачи
        function getTaskStatus(startTime, duration, completed) {
            if (completed) return 'completed';
            
            const [hours, minutes] = startTime.split(':').map(Number);
            const start = new Date();
            start.setHours(hours, minutes, 0, 0);
            const end = new Date(start.getTime() + duration * 60000);
            const now = new Date();
            
            if (now < start) return 'pending'; // Еще не началась
            if (now >= start && now < end) return 'active'; // В процессе
            if (now >= end) return 'overdue'; // Просрочена
            
            return 'pending';
        }

        function renderTasks() {
            const main = document.querySelector('#mainTasksTable tbody');
            const completed = document.querySelector('#completedTasksTable tbody');
            main.innerHTML = '';
            completed.innerHTML = '';

            const sorted = [...tasks].sort((a, b) => {
                const p = { high: 3, medium: 2, low: 1 };
                if (a.priority !== b.priority) return p[b.priority] - p[a.priority];
                return a.startTime.localeCompare(b.startTime);
            });

            sorted.forEach(task => {
                const endTime = calculateEndTime(task.startTime, task.duration);
                const status = getTaskStatus(task.startTime, task.duration, task.completed);
                
                const row = document.createElement('tr');
                
                // Добавляем статусные классы
                if (status === 'active' && !task.completed) {
                    row.classList.add('status-active');
                } else if (status === 'overdue' && !task.completed) {
                    row.classList.add('status-overdue');
                }

                row.innerHTML = `
                    <td>${task.name}</td>
                    <td>${task.description || '-'}</td>
                    <td>${task.startTime}</td>
                    <td>${task.duration} мин</td>
                    <td>${endTime}</td>
                    <td class="priority-${task.priority}">
                        ${task.priority === 'low' ? 'Низкий' :
                          task.priority === 'medium' ? 'Средний' : 'Высокий'}
                    </td>
                    <td>${status === 'pending' ? 'Ожидает' : 
                          status === 'active' ? 'В процессе' : 
                          status === 'overdue' ? 'Просрочена' : 'Выполнена'}</td>
                `;

                if (!task.completed) {
                    const actions = document.createElement('td');
                    const completeBtn = document.createElement('button');
                    completeBtn.textContent = '✅ Выполнить';
                    completeBtn.onclick = () => {
                        tasks = tasks.map(t => t.id === task.id ? { ...t, completed: true } : t);
                        saveTasks();
                        renderTasks();
                    };

                    const deleteBtn = document.createElement('button');
                    deleteBtn.textContent = '🗑️ Удалить';
                    deleteBtn.onclick = () => {
                        if (confirm("Удалить задачу?")) {
                            tasks = tasks.filter(t => t.id !== task.id);
                            saveTasks();
                            renderTasks();
                        }
                    };

                    actions.appendChild(completeBtn);
                    actions.appendChild(deleteBtn);
                    row.appendChild(actions);
                    main.appendChild(row);
                } else {
                    completed.appendChild(row);
                }
            });
        }

        document.getElementById('taskForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const name = document.getElementById('taskName').value.trim();
            const desc = document.getElementById('taskDescription').value.trim();
            const time = document.getElementById('startTime').value;
            const dur = parseInt(document.getElementById('duration').value);
            const pri = document.getElementById('priority').value;

            if (!name || !time || !dur) return alert("Заполните обязательные поля");

            // Проверяем, не просрочена ли задача сразу
            const [hours, minutes] = time.split(':').map(Number);
            const start = new Date();
            start.setHours(hours, minutes, 0, 0);
            const end = new Date(start.getTime() + dur * 60000);
            const now = new Date();
            
            if (end < now) {
                if (!confirm("Эта задача уже просрочена. Добавить?")) {
                    return;
                }
            }

            tasks.push({
                id: Date.now(),
                name,
                description: desc,
                startTime: time,
                duration: dur,
                priority: pri,
                completed: false
            });

            saveTasks();
            renderTasks();
            this.reset();
        });

        // Периодическая проверка статусов (каждую минуту)
        setInterval(renderTasks, 60000);
        
        renderTasks();
    </script>
</body>
</html>
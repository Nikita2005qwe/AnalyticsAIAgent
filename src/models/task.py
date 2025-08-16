from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime, timedelta


@dataclass
class Task:
    title: str  # Название задачи
    description: str  # Описание
    start_time: datetime  # Время начала выполнения
    duration_minutes: int  # Длительность в минутах
    complexity: str  # Сложность: "low", "medium", "high"

    # Системные поля
    status: str = "pending"  # pending, in_progress, completed, overdue
    created_date: datetime = field(default_factory=datetime.now)
    completed_date: Optional[datetime] = None
    execution_order: int = 0  # Порядок выполнения (1, 2, 3...)

    @property
    def end_time(self) -> datetime:
        """Рассчитывает время окончания"""
        return self.start_time + timedelta(minutes=self.duration_minutes)

    @property
    def is_overdue(self) -> bool:
        """Проверяет, просрочена ли задача"""
        if self.status == "completed":
            return False
        return datetime.now() > self.end_time

    @property
    def is_active(self) -> bool:
        """Проверяет, активна ли задача сейчас"""
        now = datetime.now()
        return self.start_time <= now <= self.end_time and self.status == "pending"
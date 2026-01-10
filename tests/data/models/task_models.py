from typing import List, Optional

from pydantic import BaseModel


class Task(BaseModel):
    task_id: int
    title: str
    description: Optional[str]
    priority: int
    is_completed: bool
    start_time: str
    end_time: str
    users: List
    is_deleted: bool


class TaskList(BaseModel):
    tasks: List[Task]
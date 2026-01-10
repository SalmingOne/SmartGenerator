from typing import Optional, List

from pydantic import BaseModel


class Reminder(BaseModel):
    reminder_id: int
    title: str
    description: Optional[str]
    user_id: int
    is_completed: bool
    start_time: str
    end_time: str
    is_deleted: bool


class ReminderList(BaseModel):
    reminder_list: List[Reminder]

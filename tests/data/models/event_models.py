from typing import List, Optional

from pydantic import BaseModel


class Event(BaseModel):
    event_id: Optional[int]
    title: str
    description: Optional[str]
    user_id: int
    meeting: str
    source: Optional[str]
    start_time: str
    end_time: str
    is_deleted: bool


class EventList(BaseModel):
    events: List[Event]
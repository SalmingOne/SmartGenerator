from typing import Optional, List, Dict

from pydantic import BaseModel

from data.models.team_model import Team


class User(BaseModel):
    user_id: int
    user_telegram_id: int
    phone: Optional[str]
    username: Optional[str]
    first_name: str
    last_name: str
    role_name: str
    last_login: str
    timezone: str
    teams: List[Dict]
    calendar_urls: List[Dict]
    subscribe_expiration: Optional[str]
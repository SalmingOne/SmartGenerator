from typing import Optional, List, Dict

from pydantic import BaseModel


class Team(BaseModel):
    team_id: int
    team_name: str
    description: str
    created_at: Optional[str] = None
    users: Optional[List[Dict]] = None


class TeamList(BaseModel):
    teams: List[Team]


class Member(BaseModel):
    team_id: int
    user_id: int
    is_team_admin: bool
    joined_at: str
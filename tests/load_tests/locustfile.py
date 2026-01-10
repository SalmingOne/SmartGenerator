import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests
from locust import HttpUser, task, LoadTestShape, between, constant

from tests.api.api_client import authenticate
from tests.data.urls import Urls
from tests.endponits.comments_endpoint import CommentsEndpoint
from tests.endponits.tasks_endpoint import TasksEndpoint
from tests.endponits.main_endpoint import MainEndpoint
from tests.endponits.teams_endpoint import TeamsEndpoint


class WebsiteUser(HttpUser):
    wait_time = between(1,10)
    host = Urls.base_url

    def on_start(self):
        self.login()

    def login(self):
        token = authenticate(self.client)
        self.client.headers.update({'Authorization': f'Bearer {token}'})
        MainEndpoint(self.client).get_all_by_date(datetime.now().strftime('%Y-%m-%d'))

    @task(1)
    def manage_task(self):
        task_endpoint = TasksEndpoint(self.client)
        payload = dict(
            title='Test Task',
            description='Test Task Description',
            priority=0,
            start_time=datetime.now(ZoneInfo('Europe/Moscow')).isoformat(),
            end_time=datetime.now(ZoneInfo('Europe/Moscow')).isoformat(),
            recurrence_type="NONE",
            recurrence_end_time=(datetime.now(ZoneInfo('Europe/Moscow')) + timedelta(7)).isoformat())

        task_id = task_endpoint.create_task(payload).json()['task']['task_id']
        time.sleep(5)
        payload['title'] = 'Updated Task'
        task_endpoint.update_task(task_id, payload)
        time.sleep(5)
        task_endpoint.delete_task(task_id)

    @task(3)
    def manage_comment(self):
        task_endpoint = TasksEndpoint(self.client)
        payload = dict(
            title='Test Task',
            description='Test Task Description',
            priority=0,
            start_time=datetime.now(ZoneInfo('Europe/Moscow')).isoformat(),
            end_time=datetime.now(ZoneInfo('Europe/Moscow')).isoformat(),
            recurrence_type="NONE",
            recurrence_end_time=(datetime.now(ZoneInfo('Europe/Moscow')) + timedelta(7)).isoformat())

        task_id = task_endpoint.create_task(payload).json()['task']['task_id']

        comments_endpoint = CommentsEndpoint(self.client)
        payload = dict(
            entity_type="task",
            entity_id=task_id,
            body='comment'
        )
        comments_endpoint.create_comment(payload)


    @task(1)
    def manage_team(self):
        teams_endpoint = TeamsEndpoint(self.client)
        payload = dict(
            team_name='Test Team To Delete',
            description='Team description'
        )
        team_id = teams_endpoint.create_team(team=payload)['team_id']
        time.sleep(5)
        payload = dict(
            team_id=team_id,
            user_telegram_name='wnsmir',
            is_admin=False
        )
        member_id = teams_endpoint.add_member(json=payload).user_id
        time.sleep(3)
        teams_endpoint.remove_member(team_id, member_id=member_id)
        time.sleep(2)
        teams_endpoint.delete_team(team_id)
    def on_stop(self):
        pass


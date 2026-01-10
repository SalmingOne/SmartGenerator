from datetime import datetime

import pytest

from tests.data.models.task_models import TaskList
from tests.data.urls import Urls
from tests.endponits.main_endpoint import MainEndpoint


class TasksEndpoint:
    def __init__(self, api_client):
        self.api_client = api_client

    def get_tasks_by_date(self, date):
        main_endpoint = MainEndpoint(self.api_client)
        all = main_endpoint.get_all_by_date(date)
        data = [item for item in all if item['type'] == 'task']
        try:
            tasks = TaskList(tasks=data)
            return tasks.tasks
        except Exception as e:
            pytest.fail(e)

    def create_task(self, task, files=None, user_ids=' '):
        if user_ids == ' ':
            task['user_ids'] = user_ids

        response = self.api_client.post(Urls.tasks_url, data=task, files=files)
        return response

    def delete_task(self, task_id):
        response = self.api_client.delete(url=f'{Urls.entities_url}?task_ids=[{task_id}]')
        assert response.status_code == 200

    def archive_task(self, task_id):
        response = self.api_client.delete(url=f'{Urls.entities_url}/soft?task_ids=[{task_id}]')
        assert response.status_code == 200

    def restore_task(self, task_id):
        payload = dict(
            task_ids=[task_id]
        )
        response = self.api_client.patch(url=f'{Urls.entities_url}/restore', json=payload)
        assert response.status_code == 200

    def update_task(self, task_id, task):
        response = self.api_client.put(url=f'{Urls.tasks_url}/{task_id}', json=task)
        return response

    def delete_task_by_name(self, event_name, date=datetime.now().strftime('%Y-%m-%d')):
        tasks = self.get_tasks_by_date(date)
        for task in tasks:
            if task.title == event_name:
                self.delete_task(task.task_id)

    def delete_all_tasks(self):
        tasks = self.get_tasks_by_date(datetime.now().strftime('%Y-%m-%d'))
        for task in tasks:
            self.delete_task(task.task_id)

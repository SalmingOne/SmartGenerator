from datetime import datetime, timedelta

import pytest

from tests.data.models.reminder_models import ReminderList
from tests.data.urls import Urls
from tests.endponits.main_endpoint import MainEndpoint


class RemindersEndpoint:

    def __init__(self, api_client):
        self.api_client = api_client

    def get_reminders_by_date(self, date):
        main_endpoint = MainEndpoint(self.api_client)
        all = main_endpoint.get_all_by_date(date)
        data = [item for item in all if item['type'] == 'reminder']
        try:
            reminders = ReminderList(reminder_list=data)
            return reminders.reminder_list
        except Exception as e:
            pytest.fail(e)

    def create_reminder(self, reminder, files=None, user_ids=' '):
        if user_ids == ' ':
            reminder['user_ids'] = user_ids
        response = self.api_client.post(url=Urls.reminders_url, data=reminder, files=files)
        return response

    def delete_reminder(self, reminder_id):
        response = self.api_client.delete(url=f'{Urls.entities_url}?reminder_ids=[{reminder_id}]')
        assert response.status_code == 200

    def archive_reminder(self, task_id):
        response = self.api_client.delete(url=f'{Urls.entities_url}/soft?reminder_ids=[{task_id}]')
        assert response.status_code == 200

    def restore_reminder(self, reminder_id):
        payload = dict(
            reminder_ids=[reminder_id]
        )
        response = self.api_client.patch(url=f'{Urls.entities_url}/restore', json=payload)
        assert response.status_code == 200

    def delete_reminder_by_name(self, reminder_name, date=datetime.now().strftime('%Y-%m-%d')):
        for reminder in self.get_reminders_by_date(date):
            if reminder.title == reminder_name:
                self.delete_reminder(reminder.reminder_id)

    def update_reminder(self, reminder_id, reminder):
        response = self.api_client.put(url=f'{Urls.reminders_url}/{reminder_id}', json=reminder)
        assert response.status_code == 200
        return response

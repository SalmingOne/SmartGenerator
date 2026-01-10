from datetime import datetime

import allure
import pytest

from tests.data.models.event_models import EventList
from tests.data.urls import Urls
from tests.endponits.main_endpoint import MainEndpoint


class EventsEndpoint:
    def __init__(self, api_client):
        self.api_client = api_client

    @allure.step('Получить все события пользователя')
    def get_events(self):
        response = self.api_client.get(url=Urls.events_url)
        assert response.status_code == 200
        data = response.json()
        try:
            events = EventList(events=data['events'])
            return events.events
        except Exception as e:
            pytest.fail(e)

    def get_events_by_date(self, date):
        main_endpoint = MainEndpoint(self.api_client)
        all = main_endpoint.get_all_by_date(date)
        data = [item for item in all if item['type'] == 'event']
        try:
            events = EventList(events=data)
            return events.events
        except Exception as e:
            pytest.fail(e)

    @allure.step('Создать событие')
    def create_event(self, event, files=None, user_ids=' '):
        if user_ids == ' ':
            event['user_ids'] = user_ids
        response = self.api_client.post(url=Urls.events_url, data=event, files=files)
        return response

    @allure.step('Удалить событие')
    def delete_event(self, event_id):
        response = self.api_client.delete(url=f'{Urls.entities_url}?event_ids=[{event_id}]')
        assert response.status_code == 200

    def archive_event(self, event_id):
        response = self.api_client.delete(url=f'{Urls.entities_url}/soft?event_ids=[{event_id}]')
        assert response.status_code == 200

    def restore_event(self, event_id):
        payload = dict(
            event_ids=[event_id]
        )
        response = self.api_client.patch(url=f'{Urls.entities_url}/restore', json=payload)
        assert response.status_code == 200

    @allure.step('Изменить событие')
    def update_event(self, event_id, event):
        response = self.api_client.put(url=f'{Urls.events_url}/{event_id}', json=event)
        return response

    def delete_event_by_name(self, event_name, date=datetime.now().strftime('%Y-%m-%d')):
        events = self.get_events_by_date(date)
        for event in events:
            if event.title == event_name:
                self.delete_event(event.event_id)
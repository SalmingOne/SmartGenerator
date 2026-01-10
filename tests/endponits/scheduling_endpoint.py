from tests.data.urls import Urls


class SchedulingEndpoint:
    def __init__(self, api_client):
        self.api_client = api_client

    def get_schedules(self):
        response = self.api_client.get(f"{Urls.scheduling_url}/schedules")
        assert response.status_code == 200
        return response.json()

    def create_schedule(self, schedule_data):
        response = self.api_client.post(f"{Urls.scheduling_url}/schedules", json=schedule_data)
        assert response.status_code == 201
        return response.json()

    def update_schedule_rules(self, schedule_id, rules):
        response = self.api_client.put(
            f"{Urls.scheduling_url}/schedules/{schedule_id}/rules",
            json=rules
        )
        assert response.status_code == 200
        return response.json()

    def set_schedule_methods(self, schedule_id, methods):
        response = self.api_client.put(
            f"{Urls.scheduling_url}/schedules/{schedule_id}/methods",
            json=methods
        )
        assert response.status_code == 200
        return response.json()

    def add_schedule_override(self, schedule_id, override_data):
        response = self.api_client.put(
            f"{Urls.scheduling_url}/schedules/{schedule_id}/overrides",
            json=override_data
        )
        assert response.status_code == 200
        return response.json()

    def delete_schedule(self, schedule_id):
        response = self.api_client.delete(f"{Urls.scheduling_url}/schedules/{schedule_id}")
        assert response.status_code == 204
        return response

    def get_public_schedule(self, token):
        response = self.api_client.get(f"{Urls.scheduling_url}/public/{token}")
        assert response.status_code == 200
        return response.json()

    def get_public_slots(self, token, params=None):
        response = self.api_client.get(f"{Urls.scheduling_url}/public/{token}/slots", params=params)
        assert response.status_code == 200
        return response.json()

    def create_public_appointment(self, token, appointment_data):
        response = self.api_client.post(
            f"{Urls.scheduling_url}/public/{token}/appointments",
            json=appointment_data
        )
        assert response.status_code == 201
        return response.json()

    def get_public_link(self, schedule_id):
        response = self.api_client.get(f"{Urls.scheduling_url}/schedules/{schedule_id}/public-link")
        assert response.status_code == 200
        return response.json()

    def rotate_public_link(self, schedule_id):
        response = self.api_client.post(f"{Urls.scheduling_url}/schedules/{schedule_id}/public-link/rotate")
        assert response.status_code == 200
        return response.json()

    def delete_schedule_by_name(self, schedule_name):
        schedules = self.get_schedules()
        for schedule in schedules:
            if schedule.get('name') == schedule_name or schedule.get('title') == schedule_name:
                self.delete_schedule(schedule['schedule_id'])
                return True
        return False

    def get_schedule_by_id(self, schedule_id):
        schedules = self.get_schedules()
        for schedule in schedules:
            if schedule.get('schedule_id') == schedule_id:
                return schedule
        return None
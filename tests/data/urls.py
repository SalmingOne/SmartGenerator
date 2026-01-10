import os
from dotenv import load_dotenv

load_dotenv()

class Urls:
    bot_url = os.getenv('BOT_URL')
    base_url = os.getenv('BASE_URL')
    entities_url = f'{base_url}/notifier/entities'
    events_url = f'{base_url}/notifier/events'
    events_by_date_url = f'{events_url}/dates'
    tasks_url = f'{base_url}/notifier/tasks'
    tasks_by_date_url = f'{tasks_url}/date'
    reminders_url = f'{base_url}/notifier/reminders'
    main_url = f'{base_url}/notifier'
    users_url = f'{base_url}/users'
    user_info_url = f'{base_url}/users/info'
    teams_url = f'{base_url}/teams'
    files_url = f'{base_url}/files'
    comments_url = f'{base_url}/comments'
    streams_url = f'{base_url}/stream'
    reactions_url = f'{base_url}/reactions/reactions'
    contacts_url = f'{base_url}/contacts'
    scheduling_url = f'{base_url}/notifier/scheduling'
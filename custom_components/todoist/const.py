from datetime import timedelta

DOMAIN = "todoist"
SCAN_INTERVAL = timedelta(seconds=60)

CONF_API_TOKEN = "api_token"
CONF_PROJECTS = "projects"
CONF_PROJECT_ID = "project_id"
CONF_PROJECT_NAME = "display_name"

DEFAULT_ICON = "mdi:format-list-checkbox"

INPUT_TEXT_LAST_CLOSED = "input_text.todoist_last_closed_task"
INPUT_TEXT_ALL_CLOSED = "input_text.todoist_all_closed_tasks"

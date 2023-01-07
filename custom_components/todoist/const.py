from datetime import timedelta

DOMAIN = "todoist"
SCAN_INTERVAL = timedelta(seconds=30)

CONF_API_TOKEN = "api_token"
CONF_PROJECTS = "projects"
CONF_PROJECT_ID = "project_id"
CONF_PROJECT_NAME = "display_name"

DEFAULT_ICON = "mdi:format-list-checkbox"

INPUT_TEXT_ENTITY_ID = "input_text.todoist_closed_tasks"

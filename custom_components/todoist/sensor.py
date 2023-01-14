"""Todoist integration."""
import json
import logging

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
import voluptuous as vol
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from todoist_api_python.api import TodoistAPI
from todoist_api_python.models import Task

from .const import (
    DOMAIN,  # noqa
    SCAN_INTERVAL,  # noqa
    CONF_API_TOKEN,
    CONF_PROJECTS,
    CONF_PROJECT_ID,
    CONF_PROJECT_NAME,
    DEFAULT_ICON,
    INPUT_TEXT_LAST_CLOSED,
    INPUT_TEXT_ALL_CLOSED,
    INPUT_TEXT_NEW_TASK
)

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_API_TOKEN): str,
        vol.Optional(CONF_PROJECTS): [
            {
                vol.Required(CONF_PROJECT_ID): int,
                vol.Optional(CONF_PROJECT_NAME, default=""): str
            }
        ]
    }
)


async def async_setup_platform(
        hass: HomeAssistant,
        config: ConfigType,
        add_entities: AddEntitiesCallback,
        _: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""

    if CONF_PROJECTS in config:
        for project in config[CONF_PROJECTS]:
            add_entities([TodoistSensor(hass, config[CONF_API_TOKEN], project)])


class TodoistSensor(SensorEntity):
    tasks: list[Task] = []

    def __init__(self, hass: HomeAssistant, api_token: str, config: dict) -> None:
        self.hass: HomeAssistant = hass
        self.config: dict = config
        self.project_id = config.get(CONF_PROJECT_ID)
        self.project_name = f"Project ID: {self.project_id}"
        self.project_display_name = config.get(CONF_PROJECT_NAME)
        self.project_url = ''
        self.api_token = api_token
        self.api = TodoistAPI(api_token)

    @property
    def name(self) -> str:
        return self.project_display_name or self.project_name

    @property
    def icon(self) -> str:
        return DEFAULT_ICON

    @property
    def unique_id(self) -> str:
        return f"todoist_project_{self.project_id}"

    @property
    def extra_state_attributes(self):
        return {
            "project_id": str(self.project_id),
            "tasks": [task.to_dict() for task in self.tasks or []],
        }

    def update(self):
        if not self.project_display_name:
            # Otherwise no need for an extra API call
            self.project_name = self.fetch_project_name()
        self.tasks = self.fetch_tasks()

    def fetch_project_name(self) -> str:
        """Load Todoist project's name"""
        try:
            return self.api.get_project(project_id=self.project_id).name
        except Exception as e:
            _LOGGER.warning(f"Could not load a project with id {self.project_id}", e)
            return ''

    def fetch_tasks(self) -> list[Task]:
        """Load Todoist project's tasks"""
        try:
            tasks = self.api.get_tasks(project_id=self.project_id)
        except Exception as e:
            _LOGGER.error(f"Could not load tasks for project {self.project_id}", e)
            return []

        # First show those without a due date, then sorted by due date
        tasks_undue = list(filter(lambda t: not t.due, tasks))
        tasks_due = sorted(list(filter(lambda t: t.due, tasks)),
                           key=lambda t: (t.due.date, t.due.datetime if t.due.datetime is not None else '0'))
        tasks = [*tasks_undue, *tasks_due]

        # Close tasks in case original API call failed
        closed_tasks = self.hass.states.get(INPUT_TEXT_ALL_CLOSED).state
        if closed_tasks:
            closed_tasks = json.loads(closed_tasks)
            for task in tasks[:]:
                if task.id in closed_tasks:
                    try:
                        self.api.close_task(task_id=task.id)
                        tasks.remove(task)
                    except Exception as e:
                        _LOGGER.error(f"Could not close task {task.id}", e)

        return tasks

    async def async_added_to_hass(self) -> None:
        """Complete integration setup after being added to hass.
        Used for adding state change listeners for closed/added tasks"""

        # Close selected tasks
        @callback
        async def close_task(event):
            state = self.hass.states.get(INPUT_TEXT_LAST_CLOSED).state
            if state:
                last_closed = json.loads(state)

                # Avoid multiple API calls if multiple sensors are defined
                if last_closed['project_id'] != str(self.project_id):
                    return

                try:
                    await self.hass.async_add_executor_job(close_task_api, last_closed['task_id'])
                except Exception as e:
                    _LOGGER.error(f"Could not close task {last_closed['task_id']}", e)
                    return

                await self.hass.async_add_executor_job(
                    self.hass.services.call, 'homeassistant', 'update_entity', {"entity_id": last_closed['sensor_id']}
                )

        def close_task_api(task_id: str) -> None:
            try:
                self.api.close_task(task_id=task_id)
            except Exception as e:
                _LOGGER.error(f"Could not close task {task_id}", e)

        async_track_state_change_event(self.hass, INPUT_TEXT_LAST_CLOSED, close_task)

        # Add newly created tasks
        @callback
        async def add_task(event):
            state = self.hass.states.get(INPUT_TEXT_NEW_TASK).state
            if state:
                new_task = json.loads(state)

                # Avoid multiple API calls if multiple sensors are defined
                if new_task['project_id'] != str(self.project_id):
                    return

                try:
                    await self.hass.async_add_executor_job(add_task_api, new_task['content'], new_task['project_id'])
                except Exception as e:
                    _LOGGER.error(f"Could not add new task to project {new_task['project_id']}", e)
                    return

                await self.hass.async_add_executor_job(
                    self.hass.services.call, 'homeassistant', 'update_entity', {"entity_id": new_task['sensor_id']}
                )

        def add_task_api(content: str, project_id: str) -> None:
            try:
                self.api.add_task(content=content, project_id=project_id)
            except Exception as e:
                _LOGGER.error(f"Could not add new task to project {project_id}", e)

        async_track_state_change_event(self.hass, INPUT_TEXT_NEW_TASK, add_task)

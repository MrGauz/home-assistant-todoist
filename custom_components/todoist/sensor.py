"""Todoist integration."""
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
    DOMAIN,
    SCAN_INTERVAL,
    CONF_API_TOKEN,
    CONF_PROJECTS,
    CONF_PROJECT_ID,
    CONF_PROJECT_NAME,
    DEFAULT_ICON,
    INPUT_TEXT_ENTITY_ID
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
        self.project_name = config.get(CONF_PROJECT_NAME)
        self.project_url = ''
        self.api_token = api_token
        self.api = TodoistAPI(api_token)

    @property
    def name(self) -> str:
        return self.project_name or f"Project ID: {self.project_id}"

    @property
    def icon(self) -> str:
        return DEFAULT_ICON

    @property
    def unique_id(self) -> str:
        return f"todoist_project_{self.project_id}"

    @property
    def extra_state_attributes(self):
        return {
            "project_url": self.project_url,
            "tasks": [task.to_dict() for task in self.tasks or []],
        }

    def update(self):
        self.project_name = self.project_name or self.fetch_project()[0]
        self.project_url = self.fetch_project()[1]
        self.tasks = self.fetch_tasks()

    def fetch_project(self) -> (str, str):
        """Load Todoist project's name and URL"""
        try:
            project = self.api.get_project(project_id=self.project_id)
            return project.name, project.url
        except Exception as error:
            _LOGGER.warning(f"Could not load a project with id {self.project_id}", error)
            return '', ''

    def fetch_tasks(self) -> list[Task]:
        """Load Todoist project's tasks"""
        try:
            return self.api.get_tasks(project_id=self.project_id)
        except Exception as error:
            _LOGGER.error(f"Could not load tasks for project {self.project_id}", error)
            return []

    async def async_added_to_hass(self) -> None:
        """Complete integration setup after being added to hass."""

        @callback
        async def close_task(event):
            state = self.hass.states.get(INPUT_TEXT_ENTITY_ID).state
            if state:
                close_task_sensor_id, close_task_id = state.split(':')

                try:
                    await self.hass.async_add_executor_job(close_task_api, close_task_id)
                except Exception as e:
                    _LOGGER.error("ERROR async_update(): " + str(e))
                    return

                await self.hass.async_add_executor_job(
                    self.hass.services.call, 'homeassistant', 'update_entity', {"entity_id": close_task_sensor_id}
                )

        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [INPUT_TEXT_ENTITY_ID], close_task
            )
        )

        def close_task_api(task_id: str) -> None:
            try:
                self.api.close_task(task_id=task_id)
            except Exception as error:
                _LOGGER.error(f"Could not close task {task_id}", error)

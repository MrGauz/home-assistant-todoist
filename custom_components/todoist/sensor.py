"""Todoist integration."""
import logging

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
import voluptuous as vol
from homeassistant.core import HomeAssistant
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
    DEFAULT_ICON
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
        self.api = TodoistAPI(api_token)

    @property
    def name(self) -> str:
        return self.project_name or f"Project ID: {self.project_id}"

    @property
    def icon(self) -> str:
        return DEFAULT_ICON

    @property
    def unique_id(self) -> str:
        return f"todoist_{self.project_id}_{self.project_name}_project"

    @property
    def extra_state_attributes(self):
        return {
            "tasks": [task.to_dict() for task in self.tasks or []]
        }

    def update(self):
        self.project_name = self.fetch_project_name() or self.project_name
        self.tasks = self.fetch_tasks()

    def fetch_project_name(self) -> str:
        if not self.project_name:
            try:
                return self.api.get_project(project_id=self.project_id).name
            except Exception as error:
                _LOGGER.warning(f"Could not find a project with id {self.project_id}", error)
                return ''

    def fetch_tasks(self) -> list[Task]:
        try:
            tasks = self.api.get_tasks(project_id=self.project_id)
        except Exception as error:
            _LOGGER.error(f"Could not load tasks for project {self.project_id}", error)
            return []

        return tasks

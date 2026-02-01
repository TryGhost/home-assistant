"""Sensor platform for Ghost."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GhostDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class GhostSensorEntityDescription(SensorEntityDescription):
    """Describes a Ghost sensor entity."""

    value_fn: Callable[[dict], Any]


SENSORS: tuple[GhostSensorEntityDescription, ...] = (
    GhostSensorEntityDescription(
        key="total_members",
        translation_key="total_members",
        name="Total Members",
        icon="mdi:account-group",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.get("members", {}).get("total", 0),
    ),
    GhostSensorEntityDescription(
        key="paid_members",
        translation_key="paid_members",
        name="Paid Members",
        icon="mdi:account-cash",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.get("members", {}).get("paid", 0),
    ),
    GhostSensorEntityDescription(
        key="free_members",
        translation_key="free_members",
        name="Free Members",
        icon="mdi:account-outline",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.get("members", {}).get("free", 0),
    ),
    GhostSensorEntityDescription(
        key="published_posts",
        translation_key="published_posts",
        name="Published Posts",
        icon="mdi:post",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.get("posts", {}).get("published", 0),
    ),
    GhostSensorEntityDescription(
        key="draft_posts",
        translation_key="draft_posts",
        name="Draft Posts",
        icon="mdi:file-edit-outline",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.get("posts", {}).get("drafts", 0),
    ),
    GhostSensorEntityDescription(
        key="scheduled_posts",
        translation_key="scheduled_posts",
        name="Scheduled Posts",
        icon="mdi:clock-outline",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.get("posts", {}).get("scheduled", 0),
    ),
    GhostSensorEntityDescription(
        key="latest_post",
        translation_key="latest_post",
        name="Latest Post",
        icon="mdi:newspaper",
        value_fn=lambda data: data.get("latest_post", {}).get("title") if data.get("latest_post") else None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Ghost sensors based on a config entry."""
    coordinator: GhostDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    async_add_entities(
        GhostSensorEntity(coordinator, description, entry)
        for description in SENSORS
    )


class GhostSensorEntity(CoordinatorEntity[GhostDataUpdateCoordinator], SensorEntity):
    """Representation of a Ghost sensor."""

    entity_description: GhostSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: GhostDataUpdateCoordinator,
        description: GhostSensorEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": coordinator.site_title,
            "manufacturer": "Ghost",
            "model": "Ghost",
            "configuration_url": coordinator.api.site_url,
        }

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        if self.entity_description.key == "latest_post":
            post = self.coordinator.data.get("latest_post")
            if post:
                return {
                    "url": post.get("url"),
                    "published_at": post.get("published_at"),
                    "slug": post.get("slug"),
                }
        return None

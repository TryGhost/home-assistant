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


def _get_mrr_value(data: dict) -> int | None:
    """Extract MRR value from coordinator data, converting cents to whole dollars."""
    mrr_data = data.get("mrr", {})
    if not mrr_data:
        return None
    # Get the first currency's value (usually USD)
    # MRR is stored in cents, convert to whole dollars
    for currency, value_cents in mrr_data.items():
        return round(value_cents / 100)
    return None


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
        key="comped_members",
        translation_key="comped_members",
        name="Comped Members",
        icon="mdi:account-star",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.get("members", {}).get("comped", 0),
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
    GhostSensorEntityDescription(
        key="latest_email",
        translation_key="latest_email",
        name="Latest Email",
        icon="mdi:email-newsletter",
        value_fn=lambda data: data.get("latest_email", {}).get("title") if data.get("latest_email") else None,
    ),
    GhostSensorEntityDescription(
        key="latest_email_sent",
        translation_key="latest_email_sent",
        name="Latest Email Sent",
        icon="mdi:send",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.get("latest_email", {}).get("email_count") if data.get("latest_email") else None,
    ),
    GhostSensorEntityDescription(
        key="latest_email_opened",
        translation_key="latest_email_opened",
        name="Latest Email Opened",
        icon="mdi:email-open",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.get("latest_email", {}).get("opened_count") if data.get("latest_email") else None,
    ),
    GhostSensorEntityDescription(
        key="latest_email_open_rate",
        translation_key="latest_email_open_rate",
        name="Latest Email Open Rate",
        icon="mdi:email-open-outline",
        native_unit_of_measurement="%",
        value_fn=lambda data: data.get("latest_email", {}).get("open_rate") if data.get("latest_email") else None,
    ),
    GhostSensorEntityDescription(
        key="latest_email_clicked",
        translation_key="latest_email_clicked",
        name="Latest Email Clicked",
        icon="mdi:cursor-default-click",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.get("latest_email", {}).get("clicked_count") if data.get("latest_email") else None,
    ),
    GhostSensorEntityDescription(
        key="latest_email_click_rate",
        translation_key="latest_email_click_rate",
        name="Latest Email Click Rate",
        icon="mdi:cursor-default-click-outline",
        native_unit_of_measurement="%",
        value_fn=lambda data: data.get("latest_email", {}).get("click_rate") if data.get("latest_email") else None,
    ),
    GhostSensorEntityDescription(
        key="socialweb_followers",
        translation_key="socialweb_followers",
        name="SocialWeb Followers",
        icon="mdi:account-multiple",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.get("activitypub", {}).get("followers", 0),
    ),
    GhostSensorEntityDescription(
        key="socialweb_following",
        translation_key="socialweb_following",
        name="SocialWeb Following",
        icon="mdi:account-multiple-outline",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.get("activitypub", {}).get("following", 0),
    ),
    GhostSensorEntityDescription(
        key="mrr",
        translation_key="mrr",
        name="MRR",
        icon="mdi:cash-multiple",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="USD",
        suggested_display_precision=0,
        value_fn=lambda data: _get_mrr_value(data),
    ),
    GhostSensorEntityDescription(
        key="arr",
        translation_key="arr",
        name="ARR",
        icon="mdi:cash-multiple",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="USD",
        suggested_display_precision=0,
        value_fn=lambda data: _get_mrr_value(data) * 12 if _get_mrr_value(data) else None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Ghost sensors based on a config entry."""
    coordinator: GhostDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    
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
            "manufacturer": "Ghost Foundation",
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
        elif self.entity_description.key == "latest_email":
            email = self.coordinator.data.get("latest_email")
            if email:
                return {
                    "subject": email.get("subject"),
                    "sent_at": email.get("submitted_at"),
                    "sent_to": email.get("email_count"),
                    "delivered": email.get("delivered_count"),
                    "opened": email.get("opened_count"),
                    "clicked": email.get("clicked_count"),
                    "failed": email.get("failed_count"),
                    "open_rate": email.get("open_rate"),
                    "click_rate": email.get("click_rate"),
                }
        return None

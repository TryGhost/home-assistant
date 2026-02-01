"""The Ghost integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.network import get_url, NoURLAvailableError

from .api import GhostAdminAPI
from .const import (
    CONF_ADMIN_API_KEY,
    CONF_SITE_URL,
    DOMAIN,
    WEBHOOK_EVENTS,
)
from .coordinator import GhostDataUpdateCoordinator
from .webhook import async_register_webhook, async_unregister_webhook, get_webhook_id

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

# Store webhook IDs created in Ghost for cleanup
GHOST_WEBHOOK_IDS = "ghost_webhook_ids"
WEBHOOKS_ENABLED = "webhooks_enabled"


def _get_external_url(hass: HomeAssistant) -> str | None:
    """Try to get an external URL for webhooks."""
    try:
        # This will return Nabu Casa URL if available, or configured external URL
        url = get_url(hass, allow_internal=False, prefer_cloud=True)
        # Only use HTTPS URLs for webhooks
        if url and url.startswith("https://"):
            return url
    except NoURLAvailableError:
        pass
    return None


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Ghost from a config entry."""
    site_url = entry.data[CONF_SITE_URL]
    admin_api_key = entry.data[CONF_ADMIN_API_KEY]

    api = GhostAdminAPI(site_url, admin_api_key)
    
    # Get site info for the coordinator name
    try:
        site = await api.get_site()
        site_title = site.get("title", "Ghost")
    except Exception as err:
        _LOGGER.error("Failed to connect to Ghost: %s", err)
        await api.close()
        return False

    coordinator = GhostDataUpdateCoordinator(hass, api, site_title)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        GHOST_WEBHOOK_IDS: [],
        WEBHOOKS_ENABLED: False,
    }

    # Auto-detect external URL and silently enable webhooks if available
    external_url = _get_external_url(hass)
    if external_url:
        await _setup_webhooks(hass, entry, api, site_title, external_url)
        hass.data[DOMAIN][entry.entry_id][WEBHOOKS_ENABLED] = True
    else:
        _LOGGER.debug("No external URL available, webhooks disabled for %s", site_title)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def _setup_webhooks(
    hass: HomeAssistant,
    entry: ConfigEntry,
    api: GhostAdminAPI,
    site_title: str,
    webhook_url: str,
) -> None:
    """Set up webhooks for real-time events."""
    # Register HA webhook endpoint
    webhook_id = await async_register_webhook(hass, entry.entry_id, site_title)
    
    # Build the full webhook URL that Ghost will POST to
    ha_webhook_url = f"{webhook_url}/api/webhook/{webhook_id}"
    
    _LOGGER.info("Setting up Ghost webhooks to %s", ha_webhook_url)
    
    # Create webhooks in Ghost for each event type
    # Ghost auto-associates webhooks with the integration owning the API key
    ghost_webhook_ids = []
    for event in WEBHOOK_EVENTS:
        try:
            webhook = await api.create_webhook(event, ha_webhook_url)
            webhook_id = webhook.get("id")
            if webhook_id:
                ghost_webhook_ids.append(webhook_id)
                _LOGGER.debug("Created Ghost webhook for %s: %s", event, webhook_id)
        except Exception as err:
            _LOGGER.warning("Failed to create webhook for %s: %s", event, err)
    
    # Store webhook IDs for cleanup
    hass.data[DOMAIN][entry.entry_id][GHOST_WEBHOOK_IDS] = ghost_webhook_ids
    _LOGGER.info("Created %d Ghost webhooks", len(ghost_webhook_ids))


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        entry_data = hass.data[DOMAIN].pop(entry.entry_id)
        coordinator = entry_data["coordinator"]
        
        # Clean up Ghost webhooks
        ghost_webhook_ids = entry_data.get(GHOST_WEBHOOK_IDS, [])
        for webhook_id in ghost_webhook_ids:
            try:
                await coordinator.api.delete_webhook(webhook_id)
                _LOGGER.debug("Deleted Ghost webhook %s", webhook_id)
            except Exception as err:
                _LOGGER.warning("Failed to delete Ghost webhook %s: %s", webhook_id, err)
        
        # Unregister HA webhook if it was enabled
        if entry_data.get(WEBHOOKS_ENABLED):
            async_unregister_webhook(hass, entry.entry_id)
        
        await coordinator.api.close()

    return unload_ok

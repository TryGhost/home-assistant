"""Config flow for Ghost integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback

from .api import GhostAdminAPI
from .const import (
    CONF_ADMIN_API_KEY,
    CONF_API_URL,
    CONF_ENABLE_WEBHOOKS,
    CONF_WEBHOOK_URL,
    DOMAIN,
    WEBHOOK_EVENTS,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_URL): str,
        vol.Required(CONF_ADMIN_API_KEY): str,
    }
)


class GhostConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ghost."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return GhostOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            site_url = user_input[CONF_API_URL].rstrip("/")
            admin_api_key = user_input[CONF_ADMIN_API_KEY]

            # Validate the API key format
            if ":" not in admin_api_key:
                errors["base"] = "invalid_api_key"
            else:
                # Test the connection
                api = GhostAdminAPI(site_url, admin_api_key)
                try:
                    site = await api.get_site()
                    site_title = site.get("title", "Ghost")

                    # Check if already configured
                    await self.async_set_unique_id(site_url)
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title=site_title,
                        data={
                            CONF_API_URL: site_url,
                            CONF_ADMIN_API_KEY: admin_api_key,
                        },
                    )
                except Exception as err:
                    _LOGGER.error("Failed to connect to Ghost: %s", err)
                    errors["base"] = "cannot_connect"
                finally:
                    await api.close()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "docs_url": "https://account.ghost.org/?r=settings/integrations",
            },
        )


class GhostOptionsFlow(OptionsFlow):
    """Handle Ghost options."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            enable_webhooks = user_input.get(CONF_ENABLE_WEBHOOKS, False)
            webhook_url = user_input.get(CONF_WEBHOOK_URL, "").rstrip("/")

            if enable_webhooks and not webhook_url:
                errors["base"] = "webhook_url_required"
            elif enable_webhooks:
                # Create webhooks in Ghost
                api = GhostAdminAPI(
                    self.config_entry.data[CONF_API_URL],
                    self.config_entry.data[CONF_ADMIN_API_KEY],
                )
                try:
                    from .webhook import get_webhook_id

                    webhook_id = get_webhook_id(self.config_entry.entry_id)
                    target_url = f"{webhook_url}/api/webhook/{webhook_id}"

                    # Get site title for webhook names
                    site = await api.get_site()
                    site_title = site.get("title", "Ghost")

                    # Create webhooks for each event
                    for event in WEBHOOK_EVENTS:
                        webhook_name = f"Home Assistant - {site_title} - {event}"
                        try:
                            await api.create_webhook(event, target_url, webhook_name)
                            _LOGGER.info("Created webhook for %s", event)
                        except Exception as err:
                            # Webhook might already exist
                            _LOGGER.debug("Could not create webhook %s: %s", event, err)

                except Exception as err:
                    _LOGGER.error("Failed to create webhooks: %s", err)
                    errors["base"] = "webhook_creation_failed"
                finally:
                    await api.close()

            if not errors:
                return self.async_create_entry(
                    title="",
                    data={
                        CONF_ENABLE_WEBHOOKS: enable_webhooks,
                        CONF_WEBHOOK_URL: webhook_url,
                    },
                )

        # Get current values
        current_enable = self.config_entry.options.get(CONF_ENABLE_WEBHOOKS, False)
        current_url = self.config_entry.options.get(CONF_WEBHOOK_URL, "")

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_ENABLE_WEBHOOKS, default=current_enable): bool,
                    vol.Optional(CONF_WEBHOOK_URL, default=current_url): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "events": ", ".join(WEBHOOK_EVENTS),
            },
        )

"""Config flow for Ghost integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .api import GhostAdminAPI
from .const import CONF_ADMIN_API_KEY, CONF_SITE_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SITE_URL): str,
        vol.Required(CONF_ADMIN_API_KEY): str,
    }
)


class GhostConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ghost."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            site_url = user_input[CONF_SITE_URL].rstrip("/")
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
                            CONF_SITE_URL: site_url,
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

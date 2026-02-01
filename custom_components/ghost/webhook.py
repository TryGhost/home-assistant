"""Webhook handlers for Ghost integration."""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import web
from homeassistant.components.webhook import async_register, async_unregister
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Events we care about - imported from const
from .const import WEBHOOK_EVENTS


def get_webhook_id(entry_id: str) -> str:
    """Generate webhook ID for a config entry."""
    return f"{DOMAIN}_{entry_id}"


async def async_register_webhook(
    hass: HomeAssistant,
    entry_id: str,
    site_title: str,
) -> str:
    """Register the webhook and return the webhook ID."""
    webhook_id = get_webhook_id(entry_id)
    
    async_register(
        hass,
        DOMAIN,
        f"Ghost ({site_title})",
        webhook_id,
        handle_webhook,
    )
    
    _LOGGER.debug("Registered webhook %s for %s", webhook_id, site_title)
    return webhook_id


async def async_unregister_webhook(hass: HomeAssistant, entry_id: str) -> None:
    """Unregister the webhook."""
    webhook_id = get_webhook_id(entry_id)
    async_unregister(hass, webhook_id)
    _LOGGER.debug("Unregistered webhook %s", webhook_id)


async def handle_webhook(
    hass: HomeAssistant,
    webhook_id: str,
    request: web.Request,
) -> web.Response:
    """Handle incoming webhook from Ghost."""
    try:
        payload = await request.json()
    except Exception as err:
        _LOGGER.error("Failed to parse webhook payload: %s", err)
        return web.Response(status=400, text="Invalid JSON")
    
    # Extract event info from Ghost webhook payload
    # Ghost sends the event type in the payload structure
    # The payload contains the resource that triggered it (e.g., member, post)
    
    event_type = None
    event_data: dict[str, Any] = {"webhook_id": webhook_id}
    
    # Determine event type from payload structure
    if "member" in payload:
        member = payload["member"]
        current = member.get("current", {})
        previous = member.get("previous", {})
        
        # Ghost webhook logic:
        # - member.added: current has data, previous is empty {}
        # - member.deleted: current is empty {}, previous has data
        # - member.updated: current has data, previous has changed fields only
        if not current:
            event_type = "ghost_member_deleted"
        elif not previous:
            event_type = "ghost_member_added"
        else:
            event_type = "ghost_member_updated"
        
        # Include useful member data
        member_data = current or previous
        event_data.update({
            "member_id": member_data.get("id"),
            "email": member_data.get("email"),
            "name": member_data.get("name"),
            "status": member_data.get("status"),
        })
    
    elif "post" in payload:
        post = payload["post"]
        current = post.get("current", {})
        previous = post.get("previous", {})
        
        # Detect publish/unpublish based on status change
        prev_status = previous.get("status")
        curr_status = current.get("status")
        
        if curr_status == "published" and prev_status != "published":
            event_type = "ghost_post_published"
        elif prev_status == "published" and curr_status != "published":
            event_type = "ghost_post_unpublished"
        else:
            event_type = "ghost_post_updated"
        
        post_data = current or previous
        event_data.update({
            "post_id": post_data.get("id"),
            "title": post_data.get("title"),
            "slug": post_data.get("slug"),
            "status": post_data.get("status"),
            "url": post_data.get("url"),
        })
    
    elif "page" in payload:
        page = payload["page"]
        current = page.get("current", {})
        previous = page.get("previous", {})
        
        prev_status = previous.get("status")
        curr_status = current.get("status")
        
        if curr_status == "published" and prev_status != "published":
            event_type = "ghost_page_published"
        elif prev_status == "published" and curr_status != "published":
            event_type = "ghost_page_unpublished"
        else:
            event_type = "ghost_page_updated"
        
        page_data = current or previous
        event_data.update({
            "page_id": page_data.get("id"),
            "title": page_data.get("title"),
            "slug": page_data.get("slug"),
            "status": page_data.get("status"),
            "url": page_data.get("url"),
        })
    
    if event_type:
        _LOGGER.info("Ghost webhook: %s", event_type)
        hass.bus.async_fire(event_type, event_data)
    else:
        _LOGGER.warning("Unknown Ghost webhook payload: %s", list(payload.keys()))
    
    return web.Response(status=200, text="OK")

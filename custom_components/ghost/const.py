"""Constants for the Ghost integration."""

DOMAIN = "ghost"

CONF_ADMIN_API_KEY = "admin_api_key"
CONF_API_URL = "api_url"
CONF_ENABLE_WEBHOOKS = "enable_webhooks"
CONF_WEBHOOK_URL = "webhook_url"

DEFAULT_SCAN_INTERVAL = 300  # 5 minutes

# API endpoints
ENDPOINT_SITE = "/ghost/api/admin/site/"
ENDPOINT_POSTS = "/ghost/api/admin/posts/"
ENDPOINT_MEMBERS = "/ghost/api/admin/members/"
ENDPOINT_TIERS = "/ghost/api/admin/tiers/"

# Webhook events to subscribe to
WEBHOOK_EVENTS = [
    "member.added",
    "member.edited",
    "member.deleted",
    "post.published",
]

"""Constants for the Ghost integration."""

DOMAIN = "ghost"

CONF_ADMIN_API_KEY = "admin_api_key"
CONF_SITE_URL = "site_url"

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

"""Ghost Admin API client."""

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import aiohttp

import jwt


class GhostAdminAPI:
    """Client for Ghost Admin API."""

    def __init__(self, site_url: str, admin_api_key: str) -> None:
        """Initialize the API client."""
        self.site_url = site_url.rstrip("/")
        self.admin_api_key = admin_api_key
        self._session: aiohttp.ClientSession | None = None

    def _generate_token(self) -> str:
        """Generate a JWT token for Ghost Admin API authentication."""
        # Split the API key into ID and secret
        key_id, secret = self.admin_api_key.split(":")
        
        # Decode the hex secret
        secret_bytes = bytes.fromhex(secret)
        
        # Create the token
        now = datetime.now(timezone.utc)
        payload = {
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=5)).timestamp()),
            "aud": "/admin/",
        }
        
        headers = {
            "alg": "HS256",
            "kid": key_id,
            "typ": "JWT",
        }
        
        return jwt.encode(payload, secret_bytes, algorithm="HS256", headers=headers)

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        """Close the session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _request(self, endpoint: str, params: dict | None = None) -> dict:
        """Make an authenticated request to the Ghost Admin API."""
        session = await self._get_session()
        token = self._generate_token()
        
        url = f"{self.site_url}{endpoint}"
        headers = {
            "Authorization": f"Ghost {token}",
            "Accept-Version": "v5.0",
        }
        
        async with session.get(url, headers=headers, params=params) as response:
            response.raise_for_status()
            return await response.json()

    async def get_site(self) -> dict:
        """Get site information."""
        data = await self._request("/ghost/api/admin/site/")
        return data.get("site", {})

    async def get_posts_count(self) -> dict:
        """Get post counts by status."""
        # Get published posts count
        published = await self._request(
            "/ghost/api/admin/posts/",
            {"limit": 1, "filter": "status:published"},
        )
        
        # Get draft posts count
        drafts = await self._request(
            "/ghost/api/admin/posts/",
            {"limit": 1, "filter": "status:draft"},
        )
        
        # Get scheduled posts count
        scheduled = await self._request(
            "/ghost/api/admin/posts/",
            {"limit": 1, "filter": "status:scheduled"},
        )
        
        return {
            "published": published.get("meta", {}).get("pagination", {}).get("total", 0),
            "drafts": drafts.get("meta", {}).get("pagination", {}).get("total", 0),
            "scheduled": scheduled.get("meta", {}).get("pagination", {}).get("total", 0),
        }

    async def get_members_count(self) -> dict:
        """Get member counts from stats endpoint."""
        data = await self._request("/ghost/api/admin/members/stats/count/")
        
        # Get total from response and latest day's breakdown
        total = data.get("total", 0)
        history = data.get("data", [])
        
        if history:
            latest = history[-1]
            return {
                "total": total,
                "paid": latest.get("paid", 0),
                "free": latest.get("free", 0),
                "comped": latest.get("comped", 0),
            }
        
        return {"total": total, "paid": 0, "free": 0, "comped": 0}

    async def get_latest_post(self) -> dict | None:
        """Get the most recently published post."""
        data = await self._request(
            "/ghost/api/admin/posts/",
            {"limit": 1, "order": "published_at desc", "filter": "status:published"},
        )
        posts = data.get("posts", [])
        return posts[0] if posts else None

    async def get_tiers(self) -> list:
        """Get subscription tiers."""
        data = await self._request("/ghost/api/admin/tiers/")
        return data.get("tiers", [])

    async def get_latest_email(self) -> dict | None:
        """Get the most recently sent email newsletter."""
        # Get posts that have been sent as email, ordered by most recent
        # Include email object AND count.clicks to get click tracking data
        data = await self._request(
            "/ghost/api/admin/posts/",
            {
                "limit": 10,
                "order": "published_at desc",
                "filter": "status:published",
                "include": "email,count.clicks",
            },
        )
        posts = data.get("posts", [])
        
        # Find the first post that has email data
        for post in posts:
            if post.get("email"):
                email = post["email"]
                email_count = email.get("email_count", 0)
                opened_count = email.get("opened_count", 0)
                # Click count comes from post.count.clicks, not email object
                count_data = post.get("count", {})
                clicked_count = count_data.get("clicks", 0) or 0
                
                return {
                    "title": post.get("title"),
                    "slug": post.get("slug"),
                    "published_at": post.get("published_at"),
                    "email_count": email_count,
                    "delivered_count": email.get("delivered_count", 0),
                    "opened_count": opened_count,
                    "clicked_count": clicked_count,
                    "failed_count": email.get("failed_count", 0),
                    "open_rate": round(opened_count / email_count * 100) if email_count > 0 else 0,
                    "click_rate": round(clicked_count / email_count * 100) if email_count > 0 else 0,
                    "subject": email.get("subject"),
                    "submitted_at": email.get("submitted_at"),
                }
        
        return None

    async def get_comments_count(self) -> int:
        """Get total comments count."""
        data = await self._request(
            "/ghost/api/admin/comments/",
            {"limit": 1},
        )
        return data.get("meta", {}).get("pagination", {}).get("total", 0)

    async def get_newsletters(self) -> list:
        """Get newsletters with subscriber counts."""
        data = await self._request(
            "/ghost/api/admin/newsletters/",
            {"include": "count.members"},
        )
        return data.get("newsletters", [])

    async def get_mrr(self) -> dict:
        """Get MRR (Monthly Recurring Revenue) data.
        
        Returns dict with currency keys and MRR values in cents.
        E.g., {"usd": 12284, "eur": 5000}
        """
        data = await self._request("/ghost/api/admin/members/stats/mrr/")
        
        result = {}
        for currency_data in data.get("data", []):
            currency = currency_data.get("currency", "usd")
            values = currency_data.get("data", [])
            if values:
                # Get the most recent MRR value
                latest = values[-1]
                result[currency] = latest.get("value", 0)
        
        return result

    async def get_activitypub_stats(self) -> dict:
        """Get ActivityPub follower/following counts (public endpoints)."""
        session = await self._get_session()
        headers = {"Accept": "application/activity+json"}
        
        stats = {"followers": 0, "following": 0}
        
        try:
            # Fetch followers count
            followers_url = f"{self.site_url}/.ghost/activitypub/followers/index"
            async with session.get(followers_url, headers=headers) as response:
                if response.ok:
                    data = await response.json()
                    stats["followers"] = data.get("totalItems", 0)
        except Exception:
            pass  # ActivityPub might not be enabled
        
        try:
            # Fetch following count
            following_url = f"{self.site_url}/.ghost/activitypub/following/index"
            async with session.get(following_url, headers=headers) as response:
                if response.ok:
                    data = await response.json()
                    stats["following"] = data.get("totalItems", 0)
        except Exception:
            pass  # ActivityPub might not be enabled
        
        return stats

    async def create_webhook(self, event: str, target_url: str) -> dict:
        """Create a webhook in Ghost.
        
        Ghost automatically associates the webhook with the integration
        that owns the API key being used.
        """
        session = await self._get_session()
        token = self._generate_token()
        
        url = f"{self.site_url}/ghost/api/admin/webhooks/"
        headers = {
            "Authorization": f"Ghost {token}",
            "Accept-Version": "v5.0",
            "Content-Type": "application/json",
        }
        
        payload = {
            "webhooks": [{
                "event": event,
                "target_url": target_url,
            }]
        }
        
        async with session.post(url, headers=headers, json=payload) as response:
            response.raise_for_status()
            data = await response.json()
            return data.get("webhooks", [{}])[0]

    async def delete_webhook(self, webhook_id: str) -> None:
        """Delete a webhook from Ghost."""
        session = await self._get_session()
        token = self._generate_token()
        
        url = f"{self.site_url}/ghost/api/admin/webhooks/{webhook_id}/"
        headers = {
            "Authorization": f"Ghost {token}",
            "Accept-Version": "v5.0",
        }
        
        async with session.delete(url, headers=headers) as response:
            response.raise_for_status()

    async def validate_credentials(self) -> bool:
        """Validate the API credentials."""
        try:
            await self.get_site()
            return True
        except Exception:
            return False

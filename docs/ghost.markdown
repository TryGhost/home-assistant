---
title: Ghost
description: Instructions on how to integrate Ghost with Home Assistant.
ha_category:
  - Sensor
ha_release: "2025.3"
ha_iot_class: Cloud Polling
ha_config_flow: true
ha_codeowners:
  - '@johnonolan'
ha_domain: ghost
ha_platforms:
  - sensor
ha_integration_type: service
---

The **Ghost** {% term integration %} allows you to monitor your [Ghost](https://ghost.org) publication metrics in Home Assistant, including member counts, revenue, post statistics, and email newsletter performance.

## Prerequisites

- A Ghost site (self-hosted or Ghost(Pro))
- Admin API access to your Ghost site

### Create a Ghost Admin API integration

1. Log in to your Ghost Admin panel.
2. Go to **Settings** → **Integrations**.
3. Select **Add custom integration**.
4. Give it a name (e.g., "Home Assistant").
5. Copy the **Admin API Key** — you'll need this during setup.

The Admin API Key is in the format `id:secret` (e.g., `6489...ab12:a8f9...3d4e`).

{% include integrations/config_flow.md %}

## Configuration parameters

{% configuration_basic %}
API URL:
  description: The URL of your Ghost site (e.g., `https://yoursite.ghost.io` or `https://blog.example.com`).
Admin API Key:
  description: The Admin API Key from your Ghost custom integration. Found in Ghost Admin → Settings → Integrations.
{% endconfiguration_basic %}

## Sensors

The Ghost integration provides the following sensors:

### Member metrics

| Sensor | Description |
|--------|-------------|
| Total Members | Total number of subscribers |
| Paid Members | Number of paying subscribers |
| Free Members | Number of free subscribers |
| Comped Members | Number of complimentary subscribers |

### Revenue metrics

| Sensor | Description |
|--------|-------------|
| MRR | Monthly Recurring Revenue (USD) |
| ARR | Annual Recurring Revenue (USD) |

### Content metrics

| Sensor | Description |
|--------|-------------|
| Published Posts | Number of published posts |
| Draft Posts | Number of draft posts |
| Scheduled Posts | Number of scheduled posts |
| Latest Post | Title of the most recent post |
| Total Comments | Total number of comments |

### Email newsletter metrics

| Sensor | Description |
|--------|-------------|
| Latest Email | Title of the most recent newsletter |
| Latest Email Sent | Number of emails sent |
| Latest Email Opened | Number of emails opened |
| Latest Email Open Rate | Open rate percentage |
| Latest Email Clicked | Number of link clicks |
| Latest Email Click Rate | Click rate percentage |

### SocialWeb (ActivityPub) metrics

| Sensor | Description |
|--------|-------------|
| SocialWeb Followers | Number of Fediverse followers |
| SocialWeb Following | Number of accounts being followed |

### Newsletter subscribers

For each active newsletter on your Ghost site, an additional sensor is created showing the subscriber count for that newsletter.

## Data updates

The integration {% term polling polls %} your Ghost site every 5 minutes to update sensor data.

## Webhook events

If your Home Assistant instance is accessible via HTTPS (e.g., via Nabu Casa), the integration will automatically create webhooks in Ghost to receive real-time events:

| Event | Description |
|-------|-------------|
| `ghost_member_added` | Fired when a new member signs up |
| `ghost_member_deleted` | Fired when a member is removed |
| `ghost_post_published` | Fired when a post is published |
| `ghost_post_unpublished` | Fired when a post is unpublished |

These events can be used in automations.

## Example automations

### Notify when a new member signs up

```yaml
automation:
  - alias: "New Ghost member notification"
    trigger:
      - trigger: event
        event_type: ghost_member_added
    action:
      - action: notify.mobile_app
        data:
          title: "New subscriber!"
          message: "{{ trigger.event.data.name or trigger.event.data.email }} just signed up"
```

### Announce milestone member counts

```yaml
automation:
  - alias: "Member milestone celebration"
    trigger:
      - trigger: state
        entity_id: sensor.my_ghost_site_total_members
    condition:
      - condition: template
        value_template: "{{ trigger.to_state.state | int % 100 == 0 }}"
    action:
      - action: notify.mobile_app
        data:
          title: "🎉 Milestone reached!"
          message: "You now have {{ trigger.to_state.state }} members!"
```

## Removing the integration

This integration follows standard integration removal. No extra steps are required.

{% include integrations/remove_device_service.md %}

## Troubleshooting

### Cannot connect to Ghost

- Verify your Ghost site URL is correct and accessible
- Ensure you're using `https://` (not `http://`)
- Check that your Ghost site is online

### Invalid API key

- The Admin API Key must be in the format `id:secret`
- Verify you copied the full key from Ghost Admin
- Try creating a new custom integration in Ghost

### Sensors showing unknown

- Some sensors (like MRR) require a paid Ghost(Pro) plan or Stripe integration
- Email metrics require at least one newsletter to have been sent
- SocialWeb metrics require ActivityPub to be enabled in Ghost Labs

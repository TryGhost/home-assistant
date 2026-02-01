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

- A Ghost site
- A Ghost administrator staff user account

### Create a Ghost Admin API integration

1. [Create a new custom integration in Ghost](https://account.ghost.org/?r=settings/integrations/new).
2. Give it a name (e.g., "Home Assistant").
3. Copy the **API URL**.
4. Copy the **Admin API Key**.

{% include integrations/config_flow.md %}

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

## Known limitations

- Webhook events require your Home Assistant instance to be accessible via HTTPS (e.g., via Nabu Casa). Without HTTPS, only polling updates are available.
- Revenue metrics (MRR/ARR) are only available for sites with Stripe connected.
- ActivityPub/SocialWeb metrics require Ghost 5.x or later with ActivityPub enabled.

## Removing the integration

This integration follows standard integration removal. No extra steps are required.

{% include integrations/remove_device_service.md %}

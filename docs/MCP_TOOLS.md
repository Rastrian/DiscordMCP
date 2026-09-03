# MCP Tools Reference

> Generated from `src/discord_mcp_platform/mcp/tools/*.py` and
> `src/discord_mcp_platform/security/policy.py`.

Total: **62 tools**.

| Tool | Scopes | Dry-run | Dangerous | Description |
|---|---|---|---|---|
| `discord.audit.list` | - | — | no | List audit events for a workspace, optionally filtered by guild or action type. |
| `discord.automation.draft` | - | — | no | Draft an automation from a natural language description. |
| `discord.automod.list` | guild:read | — | no | List auto-moderation rules of a Discord guild. |
| `discord.automod.get` | guild:read | — | no | Get an auto-moderation rule of a Discord guild. |
| `discord.automod.create` | guild:write | yes | yes | Create an auto-moderation rule in a Discord guild. Defaults to dry-run mode. |
| `discord.automod.update` | guild:write | yes | yes | Update an auto-moderation rule in a Discord guild. Defaults to dry-run mode. |
| `discord.automod.delete` | guild:write | yes | yes | Delete an auto-moderation rule from a Discord guild. Defaults to dry-run mode. |
| `discord.channel.list` | channel:read | — | no | List channels in a Discord guild. |
| `discord.channel.get` | channel:read | — | no | Get a Discord channel by ID. |
| `discord.channel.create` | channel:write | yes | yes | Create a channel in a Discord guild. Defaults to dry-run mode. |
| `discord.channel.edit` | channel:write | yes | yes | Edit a channel in a Discord guild. Defaults to dry-run mode. |
| `discord.channel.delete` | channel:write | yes | yes | Delete a channel from a Discord guild. Defaults to dry-run mode. |
| `discord.channel.edit_permissions` | channel:write | yes | no | Edit permission overwrites for a channel. Defaults to dry-run mode. |
| `discord.channel.delete_permissions` | channel:write | yes | no | Delete a permission overwrite for a channel. Defaults to dry-run mode. |
| `discord.pin.list` | message:read | — | no | List pinned messages in a Discord channel. |
| `discord.pin.add` | message:write | yes | no | Pin a message in a Discord channel. Defaults to dry-run mode. |
| `discord.pin.remove` | message:write | yes | no | Unpin a message from a Discord channel. Defaults to dry-run mode. |
| `discord.event.list` | guild:read | — | no | List scheduled events in a Discord guild. |
| `discord.event.get` | guild:read | — | no | Get a scheduled event of a Discord guild. |
| `discord.event.create` | guild:write | yes | yes | Create a scheduled event in a Discord guild. Defaults to dry-run mode. |
| `discord.event.update` | guild:write | yes | yes | Update a scheduled event in a Discord guild. Defaults to dry-run mode. |
| `discord.event.delete` | guild:write | yes | yes | Delete a scheduled event from a Discord guild. Defaults to dry-run mode. |
| `discord.event.list_users` | guild:read | — | no | List users interested in a scheduled event. |
| `discord.guild.list` | guild:read | — | no | List Discord guilds the bot is installed in. |
| `discord.guild.get` | guild:read | — | no | Get a Discord guild by ID. |
| `discord.guild.modify` | guild:write | yes | yes | Modify a Discord guild. Defaults to dry-run mode. |
| `discord.guild.incident_actions` | guild:write | yes | yes | Set guild incident actions (server lockdown): temporarily disable invites and/or DMs for the whole guild until the given ISO 8601 timestamps. Discord allows at most 24h ahead; pass null to re-enable. Defaults to dry-run mode. |
| `discord.invite.create` | channel:write | yes | yes | Create an invite for a Discord channel. Defaults to dry-run mode. |
| `discord.invite.list` | channel:read | — | no | List invites for a Discord guild. |
| `discord.invite.get` | channel:read | — | no | Get an invite by code. |
| `discord.invite.delete` | channel:write | yes | yes | Delete (revoke) an invite. Defaults to dry-run mode. |
| `discord.member.get` | member:read | — | no | Get a member of a Discord guild. |
| `discord.member.list` | member:read | — | no | List members of a Discord guild. |
| `discord.member.kick` | member:write | yes | yes | Kick a member from a Discord guild. Defaults to dry-run mode. |
| `discord.member.ban` | member:write | yes | yes | Ban a member from a Discord guild. Defaults to dry-run mode. |
| `discord.member.timeout` | member:write | yes | yes | Timeout a member in a Discord guild. Defaults to dry-run mode. |
| `discord.member.unban` | member:write | yes | yes | Unban a member from a Discord guild. Defaults to dry-run mode. |
| `discord.message.list_recent` | message:read | — | no | List recent messages from a Discord channel. |
| `discord.message.send` | message:write | — | yes | Send a message to a Discord channel. Defaults to dry-run mode. |
| `discord.message.get` | message:read | — | no | Get a single message from a Discord channel. |
| `discord.message.edit` | message:write | yes | yes | Edit a message in a Discord channel. Defaults to dry-run mode. |
| `discord.message.send_embed` | message:write | — | no | Send a rich embed message to a Discord channel. Defaults to dry-run mode. |
| `discord.message.delete` | moderation:write | yes | yes | Delete a single message from a Discord channel. Defaults to dry-run mode. |
| `discord.message.bulk_delete` | moderation:write | yes | yes | Bulk delete messages from a Discord channel. Defaults to dry-run mode. |
| `discord.reaction.add` | message:write | yes | yes | Add a reaction to a Discord message. |
| `discord.reaction.remove` | message:write | yes | yes | Remove the bot's reaction from a Discord message. |
| `discord.reaction.list` | message:read | — | no | List users that reacted to a Discord message with a given emoji. |
| `discord.reaction.remove_user` | message:write | yes | yes | Remove another user's reaction from a Discord message. Defaults to dry-run mode. |
| `discord.role.list` | role:read | — | no | List roles in a Discord guild. |
| `discord.role.create` | role:write | yes | yes | Create a new role in a Discord guild. Defaults to dry-run mode. |
| `discord.role.modify` | role:write | yes | yes | Modify an existing role in a Discord guild. Defaults to dry-run mode. |
| `discord.role.delete` | role:write | yes | yes | Delete a role from a Discord guild. Defaults to dry-run mode. |
| `discord.role.reorder` | role:write | yes | yes | Reorder roles in a Discord guild. |
| `discord.role.assign` | role:write | yes | yes | Assign a role to a member in a Discord guild. Defaults to dry-run mode. |
| `discord.role.remove` | role:write | yes | yes | Remove a role from a member in a Discord guild. Defaults to dry-run mode. |
| `discord.thread.create` | - | — | yes | Create a thread in a Discord channel. Defaults to dry-run mode. |
| `discord.webhook.create` | channel:write | yes | yes | Create a webhook in a Discord channel. Defaults to dry-run mode. |
| `discord.webhook.list` | channel:read | — | no | List webhooks in a Discord guild. |
| `discord.webhook.get` | channel:read | — | no | Get a webhook by ID. |
| `discord.webhook.modify` | channel:write | yes | yes | Modify a webhook. Defaults to dry-run mode. |
| `discord.webhook.delete` | channel:write | yes | yes | Delete a webhook. Defaults to dry-run mode. |
| `discord.webhook.execute` | message:write | yes | yes | Execute a webhook to send a message. Defaults to dry-run mode. |

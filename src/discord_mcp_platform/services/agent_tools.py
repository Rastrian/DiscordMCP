# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from discord_mcp_platform.app.logging import get_logger

if TYPE_CHECKING:
    from discord_mcp_platform.discord.bot_runtime import BotRuntime

log = get_logger("agent_tools")

MAX_TOOL_ITERATIONS = 10
TOOL_RETRY_ATTEMPTS = 3
TOOL_RETRY_BASE_DELAY = 1.0

TOOL_DEFINITIONS = [
    # ── Channels ──
    {
        "name": "list_channels",
        "description": "List all channels in a Discord guild.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string", "description": "The guild ID."},
            },
            "required": ["guild_id"],
        },
    },
    {
        "name": "get_channel",
        "description": "Get info about a single Discord channel.",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel_id": {"type": "string", "description": "The channel ID."},
            },
            "required": ["channel_id"],
        },
    },
    {
        "name": "create_channel",
        "description": "Create a new channel in a Discord guild. type: 0=text, 2=voice, 4=category.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string", "description": "The guild ID."},
                "name": {"type": "string", "description": "The channel name."},
                "channel_type": {
                    "type": "integer",
                    "description": "0=text, 2=voice, 4=category. Default 0.",
                    "default": 0,
                },
                "parent_id": {"type": "string", "description": "Optional parent category ID."},
                "topic": {"type": "string", "description": "Optional channel topic."},
            },
            "required": ["guild_id", "name"],
        },
    },
    {
        "name": "edit_channel",
        "description": "Edit a channel's properties (name, topic, parent, etc). Only pass fields you want to change.",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel_id": {"type": "string", "description": "The channel ID."},
                "name": {"type": "string", "description": "New name."},
                "topic": {"type": "string", "description": "New topic."},
                "parent_id": {"type": "string", "description": "Move under this category."},
                "nsfw": {"type": "boolean", "description": "NSFW flag."},
                "rate_limit_per_user": {"type": "integer", "description": "Slowmode seconds."},
            },
            "required": ["channel_id"],
        },
    },
    {
        "name": "delete_channel",
        "description": "Delete a channel or category.",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel_id": {
                    "type": "string",
                    "description": "The channel or category ID to delete.",
                },
            },
            "required": ["channel_id"],
        },
    },
    # ── Messages ──
    {
        "name": "list_messages",
        "description": "List recent messages from a Discord channel.",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel_id": {"type": "string", "description": "The channel ID."},
                "limit": {
                    "type": "integer",
                    "description": "Number of messages (1-100, default 50).",
                    "default": 50,
                },
            },
            "required": ["channel_id"],
        },
    },
    {
        "name": "send_message",
        "description": "Send a message to a Discord channel. Max 2000 chars.",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel_id": {"type": "string", "description": "The channel ID."},
                "content": {"type": "string", "description": "The message content."},
            },
            "required": ["channel_id", "content"],
        },
    },
    {
        "name": "edit_message",
        "description": "Edit an existing message.",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel_id": {"type": "string", "description": "The channel ID."},
                "message_id": {"type": "string", "description": "The message ID."},
                "content": {"type": "string", "description": "New content."},
            },
            "required": ["channel_id", "message_id", "content"],
        },
    },
    {
        "name": "delete_message",
        "description": "Delete a specific message.",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel_id": {"type": "string", "description": "The channel ID."},
                "message_id": {"type": "string", "description": "The message ID."},
            },
            "required": ["channel_id", "message_id"],
        },
    },
    {
        "name": "bulk_delete_messages",
        "description": "Bulk delete multiple messages (2-100 at once).",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel_id": {"type": "string", "description": "The channel ID."},
                "message_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of message IDs to delete (2-100).",
                },
            },
            "required": ["channel_id", "message_ids"],
        },
    },
    # ── Threads ──
    {
        "name": "create_thread",
        "description": "Create a thread in a channel.",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel_id": {"type": "string", "description": "The channel ID."},
                "name": {"type": "string", "description": "Thread name."},
                "message_id": {
                    "type": "string",
                    "description": "Optional message ID to attach thread to.",
                },
                "private": {
                    "type": "boolean",
                    "description": "Private thread. Default false.",
                    "default": False,
                },
            },
            "required": ["channel_id", "name"],
        },
    },
    # ── Roles (full CRUD) ──
    {
        "name": "list_roles",
        "description": "List all roles in a Discord guild.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string", "description": "The guild ID."},
            },
            "required": ["guild_id"],
        },
    },
    {
        "name": "create_role",
        "description": "Create a new role in a Discord guild.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string", "description": "The guild ID."},
                "name": {"type": "string", "description": "Role name."},
                "color": {
                    "type": "integer",
                    "description": "Color as RGB integer (e.g. 3447003 for blue). Default 0.",
                },
                "hoist": {
                    "type": "boolean",
                    "description": "Show separately in member list. Default false.",
                    "default": False,
                },
                "mentionable": {
                    "type": "boolean",
                    "description": "Allow @mention. Default false.",
                    "default": False,
                },
                "permissions": {
                    "type": "string",
                    "description": "Permission bits as string. Default '0'.",
                },
            },
            "required": ["guild_id", "name"],
        },
    },
    {
        "name": "edit_role",
        "description": "Edit a role's properties (name, color, hoist, mentionable). Only pass fields you want to change.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string", "description": "The guild ID."},
                "role_id": {"type": "string", "description": "The role ID."},
                "name": {"type": "string", "description": "New role name."},
                "color": {"type": "integer", "description": "New color as RGB integer."},
                "hoist": {"type": "boolean", "description": "Show separately in member list."},
                "mentionable": {"type": "boolean", "description": "Allow @mention."},
                "permissions": {"type": "string", "description": "Permission bits as string."},
            },
            "required": ["guild_id", "role_id"],
        },
    },
    {
        "name": "delete_role",
        "description": "Delete a role from a Discord guild.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string", "description": "The guild ID."},
                "role_id": {"type": "string", "description": "The role ID to delete."},
            },
            "required": ["guild_id", "role_id"],
        },
    },
    {
        "name": "reorder_roles",
        "description": "Reorder roles in a guild. Pass a list of {id, position} objects.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string", "description": "The guild ID."},
                "positions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "position": {"type": "integer"},
                        },
                        "required": ["id", "position"],
                    },
                    "description": "List of {id, position} pairs.",
                },
            },
            "required": ["guild_id", "positions"],
        },
    },
    {
        "name": "assign_role",
        "description": "Assign a role to a guild member.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string"},
                "user_id": {"type": "string"},
                "role_id": {"type": "string"},
            },
            "required": ["guild_id", "user_id", "role_id"],
        },
    },
    {
        "name": "remove_role",
        "description": "Remove a role from a guild member.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string"},
                "user_id": {"type": "string"},
                "role_id": {"type": "string"},
            },
            "required": ["guild_id", "user_id", "role_id"],
        },
    },
    # ── Members ──
    {
        "name": "list_members",
        "description": "List members of a Discord guild.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string", "description": "The guild ID."},
                "limit": {
                    "type": "integer",
                    "description": "Number of members (1-1000, default 100).",
                    "default": 100,
                },
            },
            "required": ["guild_id"],
        },
    },
    {
        "name": "get_member",
        "description": "Get info about a specific guild member.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string"},
                "user_id": {"type": "string"},
            },
            "required": ["guild_id", "user_id"],
        },
    },
    {
        "name": "kick_member",
        "description": "Kick a member from a Discord guild.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string"},
                "user_id": {"type": "string"},
            },
            "required": ["guild_id", "user_id"],
        },
    },
    {
        "name": "ban_member",
        "description": "Ban a member from a Discord guild.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string"},
                "user_id": {"type": "string"},
                "delete_message_days": {
                    "type": "integer",
                    "description": "Delete messages from last N days (0-7). Default 0.",
                    "default": 0,
                },
            },
            "required": ["guild_id", "user_id"],
        },
    },
    {
        "name": "unban_member",
        "description": "Unban a member from a Discord guild.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string"},
                "user_id": {"type": "string"},
            },
            "required": ["guild_id", "user_id"],
        },
    },
    {
        "name": "timeout_member",
        "description": "Timeout a member (mute). ISO 8601 datetime for when timeout ends.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string"},
                "user_id": {"type": "string"},
                "communication_disabled_until": {
                    "type": "string",
                    "description": "ISO 8601 datetime when timeout ends.",
                },
            },
            "required": ["guild_id", "user_id", "communication_disabled_until"],
        },
    },
    # ── Invites ──
    {
        "name": "list_invites",
        "description": "List all invites for a Discord guild.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string"},
            },
            "required": ["guild_id"],
        },
    },
    {
        "name": "create_invite",
        "description": "Create an invite for a channel.",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel_id": {"type": "string"},
                "max_uses": {
                    "type": "integer",
                    "description": "Max uses (0=unlimited). Default 0.",
                    "default": 0,
                },
                "max_age": {
                    "type": "integer",
                    "description": "Max age in seconds (0=never expires). Default 86400.",
                    "default": 86400,
                },
                "temporary": {
                    "type": "boolean",
                    "description": "Temporary membership. Default false.",
                    "default": False,
                },
            },
            "required": ["channel_id"],
        },
    },
    {
        "name": "delete_invite",
        "description": "Delete/revoke an invite by code.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "The invite code."},
            },
            "required": ["code"],
        },
    },
    # ── Guild ──
    {
        "name": "get_guild",
        "description": "Get info about a Discord guild.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string"},
            },
            "required": ["guild_id"],
        },
    },
    {
        "name": "edit_guild",
        "description": "Edit guild properties (name, etc). Only pass fields you want to change.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string"},
                "name": {"type": "string", "description": "New guild name."},
            },
            "required": ["guild_id"],
        },
    },
    # ── Pins ──
    {
        "name": "list_pinned_messages",
        "description": "List pinned messages in a channel.",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel_id": {"type": "string", "description": "The channel ID."},
            },
            "required": ["channel_id"],
        },
    },
    {
        "name": "pin_message",
        "description": "Pin a message in a channel.",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel_id": {"type": "string", "description": "The channel ID."},
                "message_id": {"type": "string", "description": "The message ID to pin."},
            },
            "required": ["channel_id", "message_id"],
        },
    },
    {
        "name": "unpin_message",
        "description": "Unpin a message from a channel.",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel_id": {"type": "string", "description": "The channel ID."},
                "message_id": {"type": "string", "description": "The message ID to unpin."},
            },
            "required": ["channel_id", "message_id"],
        },
    },
    # ── Reactions ──
    {
        "name": "add_reaction",
        "description": "Add a reaction to a message. Use Unicode emoji names or custom emoji format name:id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel_id": {"type": "string", "description": "The channel ID."},
                "message_id": {"type": "string", "description": "The message ID."},
                "emoji": {
                    "type": "string",
                    "description": "The emoji to react with (e.g. '👍' or 'customemoji:123456').",
                },
            },
            "required": ["channel_id", "message_id", "emoji"],
        },
    },
    {
        "name": "remove_reaction",
        "description": "Remove the bot's reaction from a message.",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel_id": {"type": "string", "description": "The channel ID."},
                "message_id": {"type": "string", "description": "The message ID."},
                "emoji": {"type": "string", "description": "The emoji to remove."},
            },
            "required": ["channel_id", "message_id", "emoji"],
        },
    },
    # ── Crosspost ──
    {
        "name": "crosspost_message",
        "description": "Publish (crosspost) a message in an announcement channel to all following channels.",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel_id": {"type": "string", "description": "The announcement channel ID."},
                "message_id": {"type": "string", "description": "The message ID to crosspost."},
            },
            "required": ["channel_id", "message_id"],
        },
    },
    # ── Threads (active/archived) ──
    {
        "name": "list_active_threads",
        "description": "List all active threads in a guild.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string", "description": "The guild ID."},
            },
            "required": ["guild_id"],
        },
    },
    {
        "name": "list_archived_threads",
        "description": "List archived threads in a channel.",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel_id": {"type": "string", "description": "The channel ID."},
                "archive_type": {
                    "type": "string",
                    "description": "'public' or 'private'. Default 'public'.",
                    "default": "public",
                },
            },
            "required": ["channel_id"],
        },
    },
    {
        "name": "list_thread_members",
        "description": "List members of a thread.",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel_id": {"type": "string", "description": "The thread channel ID."},
            },
            "required": ["channel_id"],
        },
    },
    # ── Audit Log ──
    {
        "name": "get_audit_log",
        "description": "Get the guild audit log. Shows recent administrative actions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string", "description": "The guild ID."},
                "user_id": {
                    "type": "string",
                    "description": "Filter by user ID who performed the action.",
                },
                "action_type": {
                    "type": "integer",
                    "description": "Filter by action type (e.g. 20=MEMBER_KICK, 22=BAN, 30=ROLE_CREATE, 40=INVITE_CREATE).",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max entries (1-100, default 50).",
                    "default": 50,
                },
            },
            "required": ["guild_id"],
        },
    },
    # ── Member Search ──
    {
        "name": "search_members",
        "description": "Search guild members by username or nickname.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string", "description": "The guild ID."},
                "query": {"type": "string", "description": "Search query (username or nickname)."},
                "limit": {
                    "type": "integer",
                    "description": "Max results (1-1000, default 25).",
                    "default": 25,
                },
            },
            "required": ["guild_id", "query"],
        },
    },
    # ── Bulk Ban ──
    {
        "name": "bulk_ban_members",
        "description": "Ban multiple members from a guild at once.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string", "description": "The guild ID."},
                "user_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user IDs to ban (up to 200).",
                },
                "delete_message_seconds": {
                    "type": "integer",
                    "description": "Delete messages from last N seconds (0-604800). Default 0.",
                    "default": 0,
                },
            },
            "required": ["guild_id", "user_ids"],
        },
    },
    # ── Prune ──
    {
        "name": "prune_members",
        "description": "Prune (kick) inactive members from a guild. Returns count of pruned members.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string", "description": "The guild ID."},
                "days": {
                    "type": "integer",
                    "description": "Number of days of inactivity (1-30, default 7).",
                    "default": 7,
                },
                "compute_prune_count": {
                    "type": "boolean",
                    "description": "Return pruned count. Default true.",
                    "default": True,
                },
            },
            "required": ["guild_id"],
        },
    },
    # ── Guild Preview ──
    {
        "name": "get_guild_preview",
        "description": "Get a guild preview (public info about the guild including member count, features, emojis).",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string", "description": "The guild ID."},
            },
            "required": ["guild_id"],
        },
    },
    # ── Onboarding (auto-role feature) ──
    {
        "name": "get_onboarding",
        "description": "Get the guild's onboarding configuration. Onboarding prompts can auto-assign roles and channels to new members.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string", "description": "The guild ID."},
            },
            "required": ["guild_id"],
        },
    },
    {
        "name": "update_onboarding",
        "description": "Update guild onboarding. Prompts have options with role_ids/channel_ids that auto-assign to new members. mode: 0=DEFAULT (only default channels), 1=ADVANCED (prompts + default channels).",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string", "description": "The guild ID."},
                "enabled": {"type": "boolean", "description": "Enable/disable onboarding."},
                "mode": {
                    "type": "integer",
                    "description": "0=DEFAULT, 1=ADVANCED. ADVANCED mode uses prompts for role/channel assignment.",
                },
                "default_channel_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Default channels new members see.",
                },
                "prompts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Prompt title shown to new members.",
                            },
                            "single_select": {
                                "type": "boolean",
                                "description": "Only allow one option. Default false.",
                            },
                            "required": {
                                "type": "boolean",
                                "description": "Must answer this prompt. Default false.",
                            },
                            "in_onboarding": {
                                "type": "boolean",
                                "description": "Show in onboarding flow. Default true.",
                            },
                            "type": {
                                "type": "integer",
                                "description": "0=MULTIPLE_CHOICE, 1=DROPDOWN.",
                            },
                            "options": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string", "description": "Option title."},
                                        "description": {
                                            "type": "string",
                                            "description": "Option description.",
                                        },
                                        "role_ids": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                            "description": "Roles to assign when this option is selected.",
                                        },
                                        "channel_ids": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                            "description": "Channels to add when this option is selected.",
                                        },
                                    },
                                    "required": ["title"],
                                },
                                "description": "Options for this prompt.",
                            },
                        },
                        "required": ["title", "options"],
                    },
                    "description": "Onboarding prompts.",
                },
            },
            "required": ["guild_id"],
        },
    },
    # ── Welcome Screen ──
    {
        "name": "get_welcome_screen",
        "description": "Get the guild's welcome screen configuration.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string", "description": "The guild ID."},
            },
            "required": ["guild_id"],
        },
    },
    {
        "name": "update_welcome_screen",
        "description": "Update the guild welcome screen shown to new members.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string", "description": "The guild ID."},
                "enabled": {"type": "boolean", "description": "Enable/disable welcome screen."},
                "description": {"type": "string", "description": "Welcome screen description."},
                "welcome_channels": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "channel_id": {"type": "string", "description": "Channel to feature."},
                            "description": {
                                "type": "string",
                                "description": "Channel description on welcome screen.",
                            },
                            "emoji_name": {"type": "string", "description": "Optional emoji name."},
                        },
                        "required": ["channel_id", "description"],
                    },
                    "description": "Channels shown on welcome screen.",
                },
            },
            "required": ["guild_id"],
        },
    },
    # ── Auto-Moderation ──
    {
        "name": "list_auto_mod_rules",
        "description": "List all auto-moderation rules in a guild.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string", "description": "The guild ID."},
            },
            "required": ["guild_id"],
        },
    },
    {
        "name": "create_auto_mod_rule",
        "description": "Create an auto-moderation rule. trigger_type: 1=KEYWORD, 3=ML_SPAM, 4=DEFAULT_KEYWORD_LIST, 5=MENTION_SPAM. event_type: 1=MESSAGE_SEND. action types: 1=BLOCK_MESSAGE, 2=FLAG_TO_CHANNEL, 3=TIMEOUT.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string", "description": "The guild ID."},
                "name": {"type": "string", "description": "Rule name."},
                "event_type": {
                    "type": "integer",
                    "description": "1=MESSAGE_SEND, 2=MEMBER_JOIN_OR_UPDATE.",
                },
                "trigger_type": {
                    "type": "integer",
                    "description": "1=KEYWORD, 3=ML_SPAM, 4=DEFAULT_KEYWORD_LIST, 5=MENTION_SPAM.",
                },
                "trigger_metadata": {
                    "type": "object",
                    "description": "Trigger config. keyword_filter/regex_patterns/allow_list for KEYWORD. mention_total_limit for MENTION_SPAM. presets for DEFAULT_KEYWORD_LIST (1=PROFANITY, 2=SEXUAL, 3=SLURS).",
                    "properties": {
                        "keyword_filter": {"type": "array", "items": {"type": "string"}},
                        "regex_patterns": {"type": "array", "items": {"type": "string"}},
                        "allow_list": {"type": "array", "items": {"type": "string"}},
                        "presets": {"type": "array", "items": {"type": "integer"}},
                        "mention_total_limit": {"type": "integer"},
                    },
                },
                "actions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "integer",
                                "description": "1=BLOCK_MESSAGE, 2=FLAG_TO_CHANNEL, 3=TIMEOUT.",
                            },
                            "metadata": {
                                "type": "object",
                                "properties": {
                                    "channel_id": {
                                        "type": "string",
                                        "description": "Channel for FLAG_TO_CHANNEL.",
                                    },
                                    "duration_seconds": {
                                        "type": "integer",
                                        "description": "Timeout duration for TIMEOUT action.",
                                    },
                                    "custom_message": {
                                        "type": "string",
                                        "description": "Custom block message for BLOCK_MESSAGE.",
                                    },
                                },
                            },
                        },
                        "required": ["type"],
                    },
                    "description": "Actions to take when triggered.",
                },
                "enabled": {
                    "type": "boolean",
                    "description": "Enable the rule. Default true.",
                    "default": True,
                },
                "exempt_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Role IDs exempt from this rule.",
                },
                "exempt_channels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Channel IDs exempt from this rule.",
                },
            },
            "required": ["guild_id", "name", "event_type", "trigger_type", "actions"],
        },
    },
    {
        "name": "update_auto_mod_rule",
        "description": "Update an existing auto-moderation rule.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string", "description": "The guild ID."},
                "rule_id": {"type": "string", "description": "The rule ID."},
                "name": {"type": "string", "description": "New rule name."},
                "enabled": {"type": "boolean", "description": "Enable/disable."},
                "trigger_metadata": {"type": "object", "description": "Updated trigger config."},
                "actions": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Updated actions.",
                },
                "exempt_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Exempt role IDs.",
                },
                "exempt_channels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Exempt channel IDs.",
                },
            },
            "required": ["guild_id", "rule_id"],
        },
    },
    {
        "name": "delete_auto_mod_rule",
        "description": "Delete an auto-moderation rule.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string", "description": "The guild ID."},
                "rule_id": {"type": "string", "description": "The rule ID."},
            },
            "required": ["guild_id", "rule_id"],
        },
    },
    # ── Scheduled Events ──
    {
        "name": "list_scheduled_events",
        "description": "List all scheduled events in a guild.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string", "description": "The guild ID."},
            },
            "required": ["guild_id"],
        },
    },
    {
        "name": "create_scheduled_event",
        "description": "Create a scheduled event. entity_type: 2=VOICE, 3=EXTERNAL. privacy_level: 2=GUILD_ONLY.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string", "description": "The guild ID."},
                "name": {"type": "string", "description": "Event name."},
                "scheduled_start_time": {"type": "string", "description": "ISO 8601 start time."},
                "scheduled_end_time": {
                    "type": "string",
                    "description": "ISO 8601 end time (required for EXTERNAL).",
                },
                "description": {"type": "string", "description": "Event description."},
                "entity_type": {"type": "integer", "description": "2=VOICE, 3=EXTERNAL."},
                "channel_id": {
                    "type": "string",
                    "description": "Voice channel ID (required for VOICE type).",
                },
                "privacy_level": {
                    "type": "integer",
                    "description": "2=GUILD_ONLY. Default 2.",
                    "default": 2,
                },
                "location": {
                    "type": "string",
                    "description": "External location (required for EXTERNAL type).",
                },
            },
            "required": ["guild_id", "name", "scheduled_start_time", "entity_type"],
        },
    },
    {
        "name": "update_scheduled_event",
        "description": "Update a scheduled event.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string", "description": "The guild ID."},
                "event_id": {"type": "string", "description": "The event ID."},
                "name": {"type": "string", "description": "New name."},
                "status": {
                    "type": "integer",
                    "description": "1=SCHEDULED, 2=ACTIVE, 3=COMPLETED, 4=CANCELED.",
                },
                "description": {"type": "string", "description": "New description."},
                "scheduled_start_time": {"type": "string", "description": "New start time."},
                "scheduled_end_time": {"type": "string", "description": "New end time."},
            },
            "required": ["guild_id", "event_id"],
        },
    },
    {
        "name": "delete_scheduled_event",
        "description": "Delete a scheduled event.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string", "description": "The guild ID."},
                "event_id": {"type": "string", "description": "The event ID."},
            },
            "required": ["guild_id", "event_id"],
        },
    },
    # ── Emojis ──
    {
        "name": "list_emojis",
        "description": "List all custom emojis in a guild.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string", "description": "The guild ID."},
            },
            "required": ["guild_id"],
        },
    },
    {
        "name": "create_emoji",
        "description": "Create a custom emoji. Image must be base64 data URI (data:image/png;base64,...).",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string", "description": "The guild ID."},
                "name": {"type": "string", "description": "Emoji name."},
                "image": {"type": "string", "description": "Base64 data URI of the emoji image."},
                "roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Role IDs that can use this emoji.",
                },
            },
            "required": ["guild_id", "name", "image"],
        },
    },
    {
        "name": "delete_emoji",
        "description": "Delete a custom emoji.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string", "description": "The guild ID."},
                "emoji_id": {"type": "string", "description": "The emoji ID."},
            },
            "required": ["guild_id", "emoji_id"],
        },
    },
    # ── Stickers ──
    {
        "name": "list_stickers",
        "description": "List all custom stickers in a guild.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string", "description": "The guild ID."},
            },
            "required": ["guild_id"],
        },
    },
    {
        "name": "delete_sticker",
        "description": "Delete a custom sticker.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string", "description": "The guild ID."},
                "sticker_id": {"type": "string", "description": "The sticker ID."},
            },
            "required": ["guild_id", "sticker_id"],
        },
    },
    # ── Vanity URL ──
    {
        "name": "get_vanity_url",
        "description": "Get the guild's vanity URL (requires Vanity URL boost level).",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string", "description": "The guild ID."},
            },
            "required": ["guild_id"],
        },
    },
    # ── Voice Regions ──
    {
        "name": "list_voice_regions",
        "description": "List available voice regions.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    # ── DM Channels ──
    {
        "name": "create_dm",
        "description": "Create a DM channel with a user.",
        "input_schema": {
            "type": "object",
            "properties": {
                "recipient_id": {"type": "string", "description": "The user ID to DM."},
            },
            "required": ["recipient_id"],
        },
    },
    # ── Guild Widget ──
    {
        "name": "get_guild_widget",
        "description": "Get the guild widget settings.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string", "description": "The guild ID."},
            },
            "required": ["guild_id"],
        },
    },
]


async def execute_tool(name: str, tool_input: dict, bot: BotRuntime) -> dict:
    for attempt in range(TOOL_RETRY_ATTEMPTS):
        try:
            return await _execute_tool_once(name, tool_input, bot)
        except Exception as e:
            error_str = str(e).lower()
            is_rate_limit = "429" in error_str or "rate" in error_str
            if is_rate_limit and attempt < TOOL_RETRY_ATTEMPTS - 1:
                delay = TOOL_RETRY_BASE_DELAY * (2**attempt)
                log.warning(
                    "agent_tool_rate_limited", tool=name, attempt=attempt + 1, retry_in=delay
                )
                await asyncio.sleep(delay)
                continue
            log.warning("agent_tool_error", tool=name, error=str(e), attempt=attempt + 1)
            return {
                "success": False,
                "error": f"FAILED to execute {name}: {e}. Tell the user the action FAILED.",
            }
    return {
        "success": False,
        "error": f"FAILED to execute {name} after {TOOL_RETRY_ATTEMPTS} attempts. Tell the user the action FAILED.",
    }


async def _execute_tool_once(name: str, tool_input: dict, bot: BotRuntime) -> dict:
    # ── Channels ──
    if name == "list_channels":
        channels = await bot.list_channels(tool_input["guild_id"])
        return {
            "success": True,
            "channels": [
                {"id": c.id, "name": c.name, "type": c.type, "parent_id": c.parent_id}
                for c in channels
            ],
        }

    if name == "get_channel":
        ch = await bot.get_channel(tool_input["channel_id"])
        return {
            "success": True,
            "id": ch.id,
            "name": ch.name,
            "type": ch.type,
            "topic": ch.topic,
            "parent_id": ch.parent_id,
        }

    if name == "create_channel":
        kwargs = {}
        for key in ("parent_id", "topic"):
            if key in tool_input:
                kwargs[key] = tool_input[key]
        ch = await bot.create_channel(
            tool_input["guild_id"],
            tool_input["name"],
            channel_type=tool_input.get("channel_type", 0),
            **kwargs,
        )
        return {"success": True, "status": "created", "channel_id": ch.id, "name": ch.name}

    if name == "edit_channel":
        kwargs = {}
        for key in ("name", "topic", "parent_id", "nsfw", "rate_limit_per_user"):
            if key in tool_input:
                kwargs[key] = tool_input[key]
        ch = await bot.modify_channel(tool_input["channel_id"], **kwargs)
        return {"success": True, "status": "updated", "channel_id": ch.id, "name": ch.name}

    if name == "delete_channel":
        await bot.delete_channel(tool_input["channel_id"])
        return {"success": True, "status": "deleted", "channel_id": tool_input["channel_id"]}

    # ── Messages ──
    if name == "list_messages":
        messages = await bot.list_recent_messages(
            tool_input["channel_id"], limit=tool_input.get("limit", 50)
        )
        return {
            "success": True,
            "messages": [
                {
                    "id": m.id,
                    "author": m.author_name,
                    "content": m.content,
                    "timestamp": m.timestamp,
                }
                for m in messages
            ],
        }

    if name == "send_message":
        msg = await bot.send_message(tool_input["channel_id"], tool_input["content"])
        return {"success": True, "status": "sent", "message_id": msg.id}

    if name == "edit_message":
        msg = await bot.edit_message(
            tool_input["channel_id"], tool_input["message_id"], tool_input["content"]
        )
        return {"success": True, "status": "edited", "message_id": msg.id}

    if name == "delete_message":
        await bot.delete_message(tool_input["channel_id"], tool_input["message_id"])
        return {"success": True, "status": "deleted", "message_id": tool_input["message_id"]}

    if name == "bulk_delete_messages":
        await bot.bulk_delete_messages(tool_input["channel_id"], tool_input["message_ids"])
        return {"success": True, "status": "deleted", "count": len(tool_input["message_ids"])}

    # ── Threads ──
    if name == "create_thread":
        thread = await bot.create_thread(
            tool_input["channel_id"],
            tool_input["name"],
            message_id=tool_input.get("message_id"),
            private=tool_input.get("private", False),
        )
        return {"success": True, "status": "created", "thread_id": thread.id, "name": thread.name}

    # ── Roles ──
    if name == "list_roles":
        roles = await bot.list_roles(tool_input["guild_id"])
        return {
            "success": True,
            "roles": [
                {
                    "id": r["id"],
                    "name": r["name"],
                    "color": r.get("color", 0),
                    "hoist": r.get("hoist", False),
                    "position": r.get("position", 0),
                    "mentionable": r.get("mentionable", False),
                }
                for r in roles
            ],
        }

    if name == "create_role":
        kwargs = {}
        for key in ("color", "hoist", "mentionable", "permissions"):
            if key in tool_input:
                kwargs[key] = tool_input[key]
        role = await bot.create_role(tool_input["guild_id"], name=tool_input["name"], **kwargs)
        return {"success": True, "status": "created", "role_id": role.id, "name": role.name}

    if name == "edit_role":
        kwargs = {}
        for key in ("name", "color", "hoist", "mentionable", "permissions"):
            if key in tool_input:
                kwargs[key] = tool_input[key]
        role = await bot.modify_role(tool_input["guild_id"], tool_input["role_id"], **kwargs)
        return {"success": True, "status": "updated", "role_id": role.id, "name": role.name}

    if name == "delete_role":
        await bot.delete_role(tool_input["guild_id"], tool_input["role_id"])
        return {"success": True, "status": "deleted", "role_id": tool_input["role_id"]}

    if name == "reorder_roles":
        await bot.reorder_roles(tool_input["guild_id"], tool_input["positions"])
        return {"success": True, "status": "reordered"}

    if name == "assign_role":
        await bot.add_role(tool_input["guild_id"], tool_input["user_id"], tool_input["role_id"])
        return {
            "success": True,
            "status": "assigned",
            "user_id": tool_input["user_id"],
            "role_id": tool_input["role_id"],
        }

    if name == "remove_role":
        await bot.remove_role(tool_input["guild_id"], tool_input["user_id"], tool_input["role_id"])
        return {
            "success": True,
            "status": "removed",
            "user_id": tool_input["user_id"],
            "role_id": tool_input["role_id"],
        }

    # ── Members ──
    if name == "list_members":
        members = await bot.list_members(tool_input["guild_id"], limit=tool_input.get("limit", 100))
        return {
            "success": True,
            "members": [
                {
                    "user_id": m.get("user", {}).get("id"),
                    "username": m.get("user", {}).get("username"),
                    "global_name": m.get("user", {}).get("global_name"),
                    "roles": m.get("roles", []),
                }
                for m in members
            ],
        }

    if name == "get_member":
        member = await bot.get_member(tool_input["guild_id"], tool_input["user_id"])
        return {
            "success": True,
            "user_id": member.get("user", {}).get("id"),
            "username": member.get("user", {}).get("username"),
            "global_name": member.get("user", {}).get("global_name"),
            "roles": member.get("roles", []),
            "joined_at": member.get("joined_at"),
        }

    if name == "kick_member":
        await bot.kick_member(tool_input["guild_id"], tool_input["user_id"])
        return {"success": True, "status": "kicked", "user_id": tool_input["user_id"]}

    if name == "ban_member":
        await bot.ban_member(
            tool_input["guild_id"],
            tool_input["user_id"],
            delete_message_days=tool_input.get("delete_message_days", 0),
        )
        return {"success": True, "status": "banned", "user_id": tool_input["user_id"]}

    if name == "unban_member":
        await bot.unban_member(tool_input["guild_id"], tool_input["user_id"])
        return {"success": True, "status": "unbanned", "user_id": tool_input["user_id"]}

    if name == "timeout_member":
        await bot.timeout_member(
            tool_input["guild_id"],
            tool_input["user_id"],
            tool_input["communication_disabled_until"],
        )
        return {"success": True, "status": "timed_out", "user_id": tool_input["user_id"]}

    # ── Invites ──
    if name == "list_invites":
        invites = await bot.list_invites(tool_input["guild_id"])
        return {
            "success": True,
            "invites": [
                {
                    "code": i.code,
                    "channel_id": i.channel_id,
                    "uses": i.uses,
                    "max_uses": i.max_uses,
                    "temporary": i.temporary,
                }
                for i in invites
            ],
        }

    if name == "create_invite":
        kwargs = {}
        for key in ("max_uses", "max_age", "temporary"):
            if key in tool_input:
                kwargs[key] = tool_input[key]
        invite = await bot.create_invite(tool_input["channel_id"], **kwargs)
        return {
            "success": True,
            "status": "created",
            "code": invite.code,
            "channel_id": invite.channel_id,
        }

    if name == "delete_invite":
        await bot.delete_invite(tool_input["code"])
        return {"success": True, "status": "deleted", "code": tool_input["code"]}

    # ── Guild ──
    if name == "get_guild":
        guild = await bot.get_guild(tool_input["guild_id"])
        return {"success": True, "id": guild.id, "name": guild.name, "icon": guild.icon}

    if name == "edit_guild":
        kwargs = {}
        for key in ("name",):
            if key in tool_input:
                kwargs[key] = tool_input[key]
        guild = await bot.modify_guild(tool_input["guild_id"], **kwargs)
        return {"success": True, "status": "updated", "id": guild.id, "name": guild.name}

    # ── Pins ──
    if name == "list_pinned_messages":
        messages = await bot.list_pinned_messages(tool_input["channel_id"])
        return {
            "success": True,
            "messages": [
                {
                    "id": m.get("id"),
                    "content": m.get("content", ""),
                    "author": m.get("author", {}).get("username", ""),
                }
                for m in messages
            ],
        }

    if name == "pin_message":
        await bot.pin_message(tool_input["channel_id"], tool_input["message_id"])
        return {"success": True, "status": "pinned", "message_id": tool_input["message_id"]}

    if name == "unpin_message":
        await bot.unpin_message(tool_input["channel_id"], tool_input["message_id"])
        return {"success": True, "status": "unpinned", "message_id": tool_input["message_id"]}

    # ── Reactions ──
    if name == "add_reaction":
        await bot.add_reaction(
            tool_input["channel_id"], tool_input["message_id"], tool_input["emoji"]
        )
        return {"success": True, "status": "reacted", "emoji": tool_input["emoji"]}

    if name == "remove_reaction":
        await bot.remove_reaction(
            tool_input["channel_id"], tool_input["message_id"], tool_input["emoji"]
        )
        return {"success": True, "status": "removed_reaction", "emoji": tool_input["emoji"]}

    # ── Crosspost ──
    if name == "crosspost_message":
        result = await bot.crosspost_message(tool_input["channel_id"], tool_input["message_id"])
        return {
            "success": True,
            "status": "crossposted",
            "message_id": result.get("id", tool_input["message_id"]),
        }

    # ── Active / Archived Threads ──
    if name == "list_active_threads":
        result = await bot.list_active_threads(tool_input["guild_id"])
        threads = result.get("threads", [])
        return {
            "success": True,
            "threads": [
                {
                    "id": t.get("id"),
                    "name": t.get("name"),
                    "parent_id": t.get("parent_id"),
                    "member_count": t.get("member_count", 0),
                }
                for t in threads
            ],
        }

    if name == "list_archived_threads":
        archive_type = tool_input.get("archive_type", "public")
        result = await bot.list_archived_threads(
            tool_input["channel_id"], archive_type=archive_type
        )
        threads = result.get("threads", [])
        return {
            "success": True,
            "threads": [
                {"id": t.get("id"), "name": t.get("name"), "parent_id": t.get("parent_id")}
                for t in threads
            ],
        }

    if name == "list_thread_members":
        members = await bot.list_thread_members(tool_input["channel_id"])
        return {
            "success": True,
            "members": [
                {"user_id": m.get("user_id"), "join_timestamp": m.get("join_timestamp")}
                for m in members
            ],
        }

    # ── Audit Log ──
    if name == "get_audit_log":
        kwargs = {}
        for key in ("user_id", "action_type", "limit"):
            if key in tool_input:
                kwargs[key] = tool_input[key]
        result = await bot.get_audit_log(tool_input["guild_id"], **kwargs)
        entries = result.get("audit_log_entries", [])
        return {
            "success": True,
            "entries": [
                {
                    "id": e.get("id"),
                    "action_type": e.get("action_type"),
                    "user_id": e.get("user_id"),
                    "target_id": e.get("target_id"),
                    "reason": e.get("reason"),
                }
                for e in entries
            ],
        }

    # ── Member Search ──
    if name == "search_members":
        members = await bot.search_members(
            tool_input["guild_id"], tool_input["query"], limit=tool_input.get("limit", 25)
        )
        return {
            "success": True,
            "members": [
                {
                    "user_id": m.get("user", {}).get("id"),
                    "username": m.get("user", {}).get("username"),
                    "global_name": m.get("user", {}).get("global_name"),
                    "nickname": m.get("nick"),
                }
                for m in members
            ],
        }

    # ── Bulk Ban ──
    if name == "bulk_ban_members":
        result = await bot.bulk_ban_members(
            tool_input["guild_id"],
            tool_input["user_ids"],
            delete_message_seconds=tool_input.get("delete_message_seconds", 0),
        )
        return {
            "success": True,
            "status": "bulk_banned",
            "banned_users": result.get("banned_users", []),
            "failed_users": result.get("failed_users", []),
        }

    # ── Prune ──
    if name == "prune_members":
        result = await bot.begin_prune(
            tool_input["guild_id"],
            days=tool_input.get("days", 7),
            compute_prune_count=tool_input.get("compute_prune_count", True),
        )
        return {"success": True, "status": "pruned", "pruned": result.get("pruned")}

    # ── Guild Preview ──
    if name == "get_guild_preview":
        result = await bot.get_guild_preview(tool_input["guild_id"])
        return {
            "success": True,
            "id": result.get("id"),
            "name": result.get("name"),
            "approximate_member_count": result.get("approximate_member_count"),
            "approximate_presence_count": result.get("approximate_presence_count"),
            "features": result.get("features", []),
        }

    # ── Onboarding ──
    if name == "get_onboarding":
        result = await bot.get_onboarding(tool_input["guild_id"])
        prompts_summary = []
        for p in result.get("prompts", []):
            options_summary = []
            for o in p.get("options", []):
                options_summary.append(
                    {
                        "title": o.get("title"),
                        "role_ids": o.get("role_ids", []),
                        "channel_ids": o.get("channel_ids", []),
                    }
                )
            prompts_summary.append(
                {
                    "title": p.get("title"),
                    "options": options_summary,
                    "required": p.get("required"),
                    "single_select": p.get("single_select"),
                }
            )
        return {
            "success": True,
            "enabled": result.get("enabled"),
            "mode": result.get("mode"),
            "default_channel_ids": result.get("default_channel_ids", []),
            "prompts": prompts_summary,
        }

    if name == "update_onboarding":
        kwargs = {}
        for key in ("enabled", "mode", "default_channel_ids", "prompts"):
            if key in tool_input:
                kwargs[key] = tool_input[key]
        result = await bot.update_onboarding(tool_input["guild_id"], **kwargs)
        return {
            "success": True,
            "status": "updated",
            "enabled": result.get("enabled"),
            "mode": result.get("mode"),
        }

    # ── Welcome Screen ──
    if name == "get_welcome_screen":
        result = await bot.get_welcome_screen(tool_input["guild_id"])
        return {
            "success": True,
            "description": result.get("description"),
            "welcome_channels": [
                {"channel_id": c.get("channel_id"), "description": c.get("description")}
                for c in result.get("welcome_channels", [])
            ],
        }

    if name == "update_welcome_screen":
        kwargs = {}
        for key in ("enabled", "description", "welcome_channels"):
            if key in tool_input:
                kwargs[key] = tool_input[key]
        result = await bot.update_welcome_screen(tool_input["guild_id"], **kwargs)
        return {"success": True, "status": "updated"}

    # ── Auto-Moderation ──
    if name == "list_auto_mod_rules":
        rules = await bot.list_auto_mod_rules(tool_input["guild_id"])
        return {
            "success": True,
            "rules": [
                {
                    "id": r.get("id"),
                    "name": r.get("name"),
                    "enabled": r.get("enabled"),
                    "trigger_type": r.get("trigger_type"),
                    "event_type": r.get("event_type"),
                }
                for r in rules
            ],
        }

    if name == "create_auto_mod_rule":
        kwargs = {}
        for key in (
            "name",
            "event_type",
            "trigger_type",
            "trigger_metadata",
            "actions",
            "enabled",
            "exempt_roles",
            "exempt_channels",
        ):
            if key in tool_input:
                kwargs[key] = tool_input[key]
        result = await bot.create_auto_mod_rule(tool_input["guild_id"], **kwargs)
        return {
            "success": True,
            "status": "created",
            "rule_id": result.get("id"),
            "name": result.get("name"),
        }

    if name == "update_auto_mod_rule":
        kwargs = {}
        for key in (
            "name",
            "enabled",
            "trigger_metadata",
            "actions",
            "exempt_roles",
            "exempt_channels",
        ):
            if key in tool_input:
                kwargs[key] = tool_input[key]
        result = await bot.update_auto_mod_rule(
            tool_input["guild_id"], tool_input["rule_id"], **kwargs
        )
        return {"success": True, "status": "updated", "rule_id": result.get("id")}

    if name == "delete_auto_mod_rule":
        await bot.delete_auto_mod_rule(tool_input["guild_id"], tool_input["rule_id"])
        return {"success": True, "status": "deleted", "rule_id": tool_input["rule_id"]}

    # ── Scheduled Events ──
    if name == "list_scheduled_events":
        events = await bot.list_scheduled_events(tool_input["guild_id"])
        return {
            "success": True,
            "events": [
                {
                    "id": e.get("id"),
                    "name": e.get("name"),
                    "scheduled_start_time": e.get("scheduled_start_time"),
                    "status": e.get("status"),
                    "entity_type": e.get("entity_type"),
                    "user_count": e.get("user_count"),
                }
                for e in events
            ],
        }

    if name == "create_scheduled_event":
        kwargs = {"privacy_level": tool_input.get("privacy_level", 2)}
        for key in (
            "name",
            "scheduled_start_time",
            "scheduled_end_time",
            "description",
            "entity_type",
            "channel_id",
        ):
            if key in tool_input:
                kwargs[key] = tool_input[key]
        if "location" in tool_input:
            kwargs["entity_metadata"] = {"location": tool_input["location"]}
        result = await bot.create_scheduled_event(tool_input["guild_id"], **kwargs)
        return {
            "success": True,
            "status": "created",
            "event_id": result.get("id"),
            "name": result.get("name"),
        }

    if name == "update_scheduled_event":
        kwargs = {}
        for key in ("name", "description", "scheduled_start_time", "scheduled_end_time", "status"):
            if key in tool_input:
                kwargs[key] = tool_input[key]
        result = await bot.update_scheduled_event(
            tool_input["guild_id"], tool_input["event_id"], **kwargs
        )
        return {"success": True, "status": "updated", "event_id": result.get("id")}

    if name == "delete_scheduled_event":
        await bot.delete_scheduled_event(tool_input["guild_id"], tool_input["event_id"])
        return {"success": True, "status": "deleted", "event_id": tool_input["event_id"]}

    # ── Emojis ──
    if name == "list_emojis":
        emojis = await bot.list_emojis(tool_input["guild_id"])
        return {
            "success": True,
            "emojis": [
                {
                    "id": e.get("id"),
                    "name": e.get("name"),
                    "animated": e.get("animated", False),
                    "available": e.get("available", True),
                }
                for e in emojis
            ],
        }

    if name == "create_emoji":
        kwargs = {}
        for key in ("name", "image", "roles"):
            if key in tool_input:
                kwargs[key] = tool_input[key]
        result = await bot.create_emoji(tool_input["guild_id"], **kwargs)
        return {
            "success": True,
            "status": "created",
            "emoji_id": result.get("id"),
            "name": result.get("name"),
        }

    if name == "delete_emoji":
        await bot.delete_emoji(tool_input["guild_id"], tool_input["emoji_id"])
        return {"success": True, "status": "deleted", "emoji_id": tool_input["emoji_id"]}

    # ── Stickers ──
    if name == "list_stickers":
        stickers = await bot.list_stickers(tool_input["guild_id"])
        return {
            "success": True,
            "stickers": [
                {
                    "id": s.get("id"),
                    "name": s.get("name"),
                    "description": s.get("description"),
                    "tags": s.get("tags"),
                }
                for s in stickers
            ],
        }

    if name == "delete_sticker":
        await bot.delete_sticker(tool_input["guild_id"], tool_input["sticker_id"])
        return {"success": True, "status": "deleted", "sticker_id": tool_input["sticker_id"]}

    # ── Vanity URL ──
    if name == "get_vanity_url":
        result = await bot.get_vanity_url(tool_input["guild_id"])
        return {"success": True, "code": result.get("code"), "uses": result.get("uses")}

    # ── Voice Regions ──
    if name == "list_voice_regions":
        regions = await bot.list_voice_regions()
        return {
            "success": True,
            "regions": [
                {"id": r.get("id"), "name": r.get("name"), "optimal": r.get("optimal")}
                for r in regions
            ],
        }

    # ── DM Channels ──
    if name == "create_dm":
        result = await bot.create_dm(tool_input["recipient_id"])
        return {"success": True, "channel_id": result.get("id")}

    # ── Guild Widget ──
    if name == "get_guild_widget":
        result = await bot.get_guild_widget(tool_input["guild_id"])
        return {
            "success": True,
            "enabled": result.get("enabled"),
            "channel_id": result.get("channel_id"),
        }

    return {"success": False, "error": f"Unknown tool: {name}"}

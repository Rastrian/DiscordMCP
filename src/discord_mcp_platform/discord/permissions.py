# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from discord_mcp_platform.app.logging import get_logger
from discord_mcp_platform.discord.bot_runtime import BotRuntime
from discord_mcp_platform.errors import DiscordPermissionError

log = get_logger("discord_permissions")

VIEW_CHANNEL: int = 0x400
SEND_MESSAGES: int = 0x800
MANAGE_CHANNELS: int = 0x10
MANAGE_GUILD: int = 0x20
READ_MESSAGE_HISTORY: int = 0x10000
MANAGE_MESSAGES: int = 0x2000
MANAGE_ROLES: int = 0x10000000
KICK_MEMBERS: int = 0x2
BAN_MEMBERS: int = 0x4
ADMINISTRATOR: int = 0x8
MANAGE_WEBHOOKS: int = 0x2000000
CREATE_INVITE: int = 0x1
TIMEOUT_MEMBERS: int = 0x400000000


def has_permission(permission_bits: int, flag: int) -> bool:
    return (permission_bits & flag) == flag


def compute_permissions_from_roles(
    bot_role_ids: list[str], guild_roles: list[dict], is_owner: bool = False
) -> int:
    if is_owner:
        return ADMINISTRATOR

    everyone_perms = 0
    role_map: dict[str, int] = {}

    for role in guild_roles:
        role_id = str(role["id"])
        perms = int(role.get("permissions", 0))
        role_map[role_id] = perms
        if role_id == str(guild_roles[0]["id"]) if guild_roles else False:
            everyone_perms = perms

    # @everyone perms are the base
    computed = everyone_perms
    for rid in bot_role_ids:
        computed |= role_map.get(rid, 0)

    return computed


def can_send_messages(guild_permissions: int) -> bool:
    return has_permission(guild_permissions, SEND_MESSAGES)


def can_read_messages(guild_permissions: int) -> bool:
    return has_permission(guild_permissions, VIEW_CHANNEL)


def can_manage_channels(guild_permissions: int) -> bool:
    return has_permission(guild_permissions, MANAGE_CHANNELS)


def can_manage_guild(guild_permissions: int) -> bool:
    return has_permission(guild_permissions, MANAGE_GUILD)


def can_read_message_history(guild_permissions: int) -> bool:
    return has_permission(guild_permissions, READ_MESSAGE_HISTORY)


def can_manage_messages(guild_permissions: int) -> bool:
    return has_permission(guild_permissions, MANAGE_MESSAGES)


def can_kick_members(guild_permissions: int) -> bool:
    return has_permission(guild_permissions, KICK_MEMBERS)


def can_ban_members(guild_permissions: int) -> bool:
    return has_permission(guild_permissions, BAN_MEMBERS)


def can_manage_roles(guild_permissions: int) -> bool:
    return has_permission(guild_permissions, MANAGE_ROLES)


def can_manage_webhooks(guild_permissions: int) -> bool:
    return has_permission(guild_permissions, MANAGE_WEBHOOKS)


def can_timeout_members(guild_permissions: int) -> bool:
    return has_permission(guild_permissions, TIMEOUT_MEMBERS)


def is_administrator(guild_permissions: int) -> bool:
    return has_permission(guild_permissions, ADMINISTRATOR)


# Map operations to required Discord permission bits
OPERATION_PERMISSIONS: dict[str, int] = {
    "message.send": SEND_MESSAGES,
    "message.read": VIEW_CHANNEL | READ_MESSAGE_HISTORY,
    "message.delete": MANAGE_MESSAGES,
    "message.bulk_delete": MANAGE_MESSAGES,
    "message.edit": SEND_MESSAGES,
    "channel.read": VIEW_CHANNEL,
    "channel.create": MANAGE_CHANNELS,
    "channel.delete": MANAGE_CHANNELS,
    "channel.modify": MANAGE_CHANNELS,
    "channel.permission_overwrite": MANAGE_ROLES,
    "thread.create": SEND_MESSAGES,
    "thread.read": VIEW_CHANNEL,
    "role.read": MANAGE_ROLES,
    "role.assign": MANAGE_ROLES,
    "role.remove": MANAGE_ROLES,
    "role.create": MANAGE_ROLES,
    "role.modify": MANAGE_ROLES,
    "role.delete": MANAGE_ROLES,
    "member.kick": KICK_MEMBERS,
    "member.ban": BAN_MEMBERS,
    "member.timeout": TIMEOUT_MEMBERS,
    "member.unban": BAN_MEMBERS,
    "webhook.create": MANAGE_WEBHOOKS,
    "webhook.list": MANAGE_WEBHOOKS,
    "webhook.modify": MANAGE_WEBHOOKS,
    "webhook.delete": MANAGE_WEBHOOKS,
    "webhook.execute": MANAGE_WEBHOOKS,
    "guild.read": VIEW_CHANNEL,
    "guild.modify": MANAGE_GUILD,
    "invite.create": CREATE_INVITE,
    "invite.list": MANAGE_GUILD,
    "invite.delete": MANAGE_GUILD,
}


async def check_discord_permission(bot: BotRuntime, guild_id: str, operation: str) -> None:
    required = OPERATION_PERMISSIONS.get(operation)
    if required is None:
        return

    try:
        guild_data = await bot.rest.get_guild(guild_id)
        is_owner = guild_data.get("owner_id") == str(bot.bot_id)

        bot_member = await bot.get_member(guild_id, str(bot.bot_id))
        bot_role_ids = [str(rid) for rid in bot_member.get("roles", [])]

        guild_roles = await bot.list_roles(guild_id)

        perms = compute_permissions_from_roles(bot_role_ids, guild_roles, is_owner)
    except Exception as e:
        log.warning("discord_permission_check_failed", guild_id=guild_id, error=str(e))
        return

    if is_administrator(perms):
        return

    if not has_permission(perms, required):
        raise DiscordPermissionError(
            f"bot lacks permission for {operation} in guild {guild_id} "
            f"(has {perms:#x}, needs {required:#x})"
        )

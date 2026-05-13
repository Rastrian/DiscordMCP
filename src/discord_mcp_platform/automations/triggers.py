# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from discord_mcp_platform.automations.definitions import TriggerType


class TriggerEvaluator:
    def evaluate(self, trigger_type: TriggerType, trigger_config: dict, context: dict) -> bool:
        if trigger_type == TriggerType.MESSAGE_CREATED:
            return self._check_message_created(trigger_config, context)
        elif trigger_type == TriggerType.MEMBER_JOINED:
            return self._check_member_joined(trigger_config, context)
        elif trigger_type == TriggerType.REACTION_ADDED:
            return self._check_reaction_added(trigger_config, context)
        elif trigger_type == TriggerType.SCHEDULED:
            return self._check_scheduled(trigger_config, context)
        return False

    def _check_message_created(self, config: dict, ctx: dict) -> bool:
        if ctx.get("event_type") != "MESSAGE_CREATE":
            return False
        channel_id = config.get("channel_id")
        if channel_id and str(ctx.get("channel_id")) != str(channel_id):
            return False
        content_match = config.get("content_contains")
        if content_match and content_match.lower() not in ctx.get("content", "").lower():
            return False
        return True

    def _check_member_joined(self, config: dict, ctx: dict) -> bool:
        return ctx.get("event_type") == "GUILD_MEMBER_ADD"

    def _check_reaction_added(self, config: dict, ctx: dict) -> bool:
        if ctx.get("event_type") != "MESSAGE_REACTION_ADD":
            return False
        emoji = config.get("emoji")
        if emoji and str(ctx.get("emoji", {}).get("name")) != str(emoji):
            return False
        return True

    def _check_scheduled(self, config: dict, ctx: dict) -> bool:
        return ctx.get("event_type") == "SCHEDULED_TICK"

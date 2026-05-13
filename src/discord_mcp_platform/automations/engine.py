# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from typing import TYPE_CHECKING

from discord_mcp_platform.app.logging import get_logger
from discord_mcp_platform.automations.evaluators import Evaluator
from discord_mcp_platform.automations.actions import ActionExecutor
from discord_mcp_platform.automations.definitions import ActionType

if TYPE_CHECKING:
    from discord_mcp_platform.discord.bot_runtime import BotRuntime

log = get_logger("automation_engine")


class AutomationEngine:
    def __init__(self, bot: BotRuntime | None = None) -> None:
        self._evaluator = Evaluator()
        self._action_executor = ActionExecutor(bot)

    async def evaluate(self, automations: list[dict], context: dict) -> list[dict]:
        results = []
        for automation in automations:
            if self._evaluator.evaluate(automation, context):
                result = await self.execute(automation, context)
                results.append({"automation_id": automation.get("id"), "result": result})
        return results

    async def execute(self, automation: dict, context: dict) -> dict:
        action_type_str = automation.get("action_type", "")
        try:
            action_type = ActionType(action_type_str)
        except ValueError:
            return {"status": "error", "error": f"unknown_action_type: {action_type_str}"}
        action_config = automation.get("action_config", {})
        try:
            result = await self._action_executor.execute(action_type, action_config, context)
            log.info(
                "automation_executed", automation_id=automation.get("id"), action=action_type_str
            )
            return result
        except Exception as e:
            log.error(
                "automation_execution_failed", automation_id=automation.get("id"), error=str(e)
            )
            return {"status": "error", "error": str(e)}

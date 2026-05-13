# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from discord_mcp_platform.automations.triggers import TriggerEvaluator
from discord_mcp_platform.automations.definitions import TriggerType


class Evaluator:
    def __init__(self) -> None:
        self._trigger_evaluator = TriggerEvaluator()

    def evaluate(self, automation: dict, context: dict) -> bool:
        trigger_type_str = automation.get("trigger_type", "")
        try:
            trigger_type = TriggerType(trigger_type_str)
        except ValueError:
            return False
        trigger_config = automation.get("trigger_config", {})
        return self._trigger_evaluator.evaluate(trigger_type, trigger_config, context)

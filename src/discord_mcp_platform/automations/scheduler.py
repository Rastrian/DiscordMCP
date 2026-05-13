# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from discord_mcp_platform.app.logging import get_logger

log = get_logger("automation_scheduler")


class AutomationScheduler:
    def __init__(self) -> None:
        self._tasks: dict[str, asyncio.Task] = {}
        self._running = False

    async def start(self, interval_seconds: int = 60, tick_callback=None) -> None:
        self._running = True
        log.info("scheduler_started", interval=interval_seconds)
        while self._running:
            try:
                if tick_callback:
                    await tick_callback(
                        {
                            "event_type": "SCHEDULED_TICK",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        },
                    )
            except Exception as e:
                log.error("scheduler_tick_error", error=str(e))
            await asyncio.sleep(interval_seconds)

    def stop(self) -> None:
        self._running = False
        for task in self._tasks.values():
            task.cancel()
        self._tasks.clear()
        log.info("scheduler_stopped")

    def schedule(self, automation_id: str, coro) -> None:
        if automation_id in self._tasks:
            self._tasks[automation_id].cancel()
        self._tasks[automation_id] = asyncio.create_task(coro)

    def cancel(self, automation_id: str) -> None:
        if automation_id in self._tasks:
            self._tasks[automation_id].cancel()
            del self._tasks[automation_id]

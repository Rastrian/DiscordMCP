# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

import asyncio
import json
import time
from collections import deque
from typing import TYPE_CHECKING, Callable

import httpx

from discord_mcp_platform.app.logging import get_logger
from discord_mcp_platform.security.allowlist import Allowlist
from discord_mcp_platform.services.agent_tools import (
    TOOL_DEFINITIONS,
    execute_tool,
    MAX_TOOL_ITERATIONS,
)

if TYPE_CHECKING:
    from discord_mcp_platform.discord.bot_runtime import BotRuntime

log = get_logger("agent_service")


class AgentService:
    def __init__(
        self,
        bot: BotRuntime,
        allowlist: Allowlist,
        api_base_url: str,
        api_key: str,
        model: str,
        system_prompt: str,
        max_history: int = 20,
        cooldown_seconds: int = 5,
        session_factory: Callable | None = None,
    ) -> None:
        self._bot = bot
        self._allowlist = allowlist
        self._api_base_url = api_base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._system_prompt = system_prompt
        self._max_history = max_history
        self._cooldown_seconds = cooldown_seconds
        self._session_factory = session_factory

        self._history: dict[str, deque[dict]] = {}
        self._cooldowns: dict[str, float] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._http_client: httpx.AsyncClient | None = None

    def _get_lock(self, channel_id: str) -> asyncio.Lock:
        if channel_id not in self._locks:
            self._locks[channel_id] = asyncio.Lock()
        return self._locks[channel_id]

    def _get_http_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=60.0)
        return self._http_client

    async def close(self) -> None:
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    # --- Mention detection ---

    def is_mentioned(self, event: dict) -> bool:
        content = event.get("content", "")
        bot_id = self._bot.bot_id
        if not bot_id:
            return False
        return f"<@{bot_id}>" in content or f"<@!{bot_id}>" in content

    def _strip_mention(self, content: str) -> str:
        bot_id = self._bot.bot_id
        if not bot_id:
            return content
        content = content.replace(f"<@!{bot_id}>", "").replace(f"<@{bot_id}>", "")
        return content.strip()

    # --- Allowlist / cooldown ---

    async def is_allowed(self, event: dict) -> bool:
        guild_id = event.get("guild_id", "")
        channel_id = event.get("channel_id", "")
        if not self._allowlist.is_guild_allowed(guild_id):
            return False
        if self._session_factory is not None:
            return await self._is_channel_in_db(channel_id, guild_id)
        return self._allowlist.is_channel_allowed(channel_id)

    async def _is_channel_in_db(self, channel_id: str, guild_id: str) -> bool:
        from sqlalchemy import select
        from discord_mcp_platform.db.models import AllowedChatChannel

        try:
            async with self._session_factory() as session:
                result = (
                    await session.execute(
                        select(AllowedChatChannel).where(
                            AllowedChatChannel.guild_id == guild_id,
                            AllowedChatChannel.channel_id == channel_id,
                        )
                    )
                ).scalar_one_or_none()
                return result is not None
        except Exception as e:
            log.warning("agent_db_allowlist_error", error=str(e))
            return self._allowlist.is_channel_allowed(channel_id)

    def _check_cooldown(self, user_id: str) -> bool:
        now = time.monotonic()
        last = self._cooldowns.get(user_id, 0.0)
        return now - last >= self._cooldown_seconds

    def _mark_cooldown(self, user_id: str) -> None:
        self._cooldowns[user_id] = time.monotonic()

    # --- Ignore own / bot messages ---

    def _is_own_message(self, event: dict) -> bool:
        author = event.get("author", {})
        return str(author.get("id", "")) == str(self._bot.bot_id or "")

    def _is_bot_message(self, event: dict) -> bool:
        author = event.get("author", {})
        return author.get("bot", False)

    # --- Conversation history ---

    def _add_to_history(self, channel_id: str, role: str, content) -> None:
        if channel_id not in self._history:
            self._history[channel_id] = deque(maxlen=self._max_history)
        self._history[channel_id].append({"role": role, "content": content})

    def _get_history(self, channel_id: str) -> list[dict]:
        return list(self._history.get(channel_id, []))

    # --- Main handler ---

    async def handle_message(self, event: dict) -> None:
        if event.get("event_type") != "MESSAGE_CREATE":
            return

        if self._is_own_message(event) or self._is_bot_message(event):
            return

        if not self.is_mentioned(event):
            return

        log.info(
            "agent_mentioned",
            channel_id=event.get("channel_id"),
            content=event.get("content", "")[:100],
        )

        if not await self.is_allowed(event):
            log.warning(
                "agent_blocked_by_allowlist",
                guild_id=event.get("guild_id"),
                channel_id=event.get("channel_id"),
            )
            return

        author = event.get("author", {})
        user_id = str(author.get("id", ""))
        channel_id = event.get("channel_id", "")
        guild_id = event.get("guild_id", "")
        raw_content = event.get("content", "")

        if not self._check_cooldown(user_id):
            log.debug("agent_cooldown", user_id=user_id, channel_id=channel_id)
            return

        user_message = self._strip_mention(raw_content)
        if not user_message:
            return

        author_name = author.get("global_name") or author.get("username", "User")
        self._add_to_history(channel_id, "user", f"{author_name}: {user_message}")

        lock = self._get_lock(channel_id)
        async with lock:
            try:
                response_text = await self._call_llm(channel_id, guild_id)
            except Exception as e:
                log.error("agent_llm_error", error=str(e), channel_id=channel_id)
                return

        if not response_text:
            return

        self._add_to_history(channel_id, "assistant", response_text)
        self._mark_cooldown(user_id)

        if len(response_text) > 2000:
            response_text = response_text[:1997] + "..."

        try:
            await self._bot.send_message(channel_id, response_text)
            log.info("agent_responded", channel_id=channel_id, user_id=user_id)
        except Exception as e:
            log.error("agent_send_error", error=str(e), channel_id=channel_id)

    # --- LLM API call with tool-use loop ---

    async def _call_llm(self, channel_id: str, guild_id: str = "") -> str | None:
        messages = self._get_history(channel_id)

        system_prompt = self._system_prompt
        if guild_id:
            system_prompt += f"\n\nContext: guild_id={guild_id}, channel_id={channel_id}. Always use this guild_id when tools require it. Never ask the user for guild_id."

        payload = {
            "model": self._model,
            "max_tokens": 1500,
            "system": system_prompt,
            "messages": messages,
            "tools": TOOL_DEFINITIONS,
        }

        headers = {
            "content-type": "application/json",
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
        }

        client = self._get_http_client()

        for _ in range(MAX_TOOL_ITERATIONS):
            response = await client.post(
                f"{self._api_base_url}/v1/messages",
                json=payload,
                headers=headers,
            )

            if response.status_code != 200:
                log.warning(
                    "agent_llm_api_error",
                    status=response.status_code,
                    body=response.text[:500],
                )
                return None

            data = response.json()
            content_blocks = data.get("content", [])
            stop_reason = data.get("stop_reason", "")

            if stop_reason != "tool_use":
                text_parts = [
                    block["text"] for block in content_blocks if block.get("type") == "text"
                ]
                return "\n".join(text_parts).strip() or None

            # Process tool_use blocks
            tool_use_blocks = [b for b in content_blocks if b.get("type") == "tool_use"]
            tool_results = []

            for block in tool_use_blocks:
                tool_name = block["name"]
                tool_input = block.get("input", {})
                tool_use_id = block["id"]

                log.info("agent_tool_call", tool=tool_name, input=tool_input)

                result = await execute_tool(tool_name, tool_input, self._bot)

                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": json.dumps(result),
                    }
                )

            # Append assistant message and tool results to conversation
            payload["messages"].append({"role": "assistant", "content": content_blocks})
            payload["messages"].append({"role": "user", "content": tool_results})

        log.warning("agent_max_tool_iterations", channel_id=channel_id)
        return "I reached the maximum number of actions. Please try again."

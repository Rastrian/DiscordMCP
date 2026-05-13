# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING, Callable, Awaitable

from discord_mcp_platform.app.logging import get_logger

if TYPE_CHECKING:
    from websockets.asyncio.client import ClientConnection

log = get_logger("discord_gateway")

GATEWAY_URL = "wss://gateway.discord.gg/?v=10&encoding=json"

# Gateway Opcodes
OP_DISPATCH = 0
OP_HEARTBEAT = 1
OP_IDENTIFY = 2
OP_RESUME = 6
OP_RECONNECT = 7
OP_INVALID_SESSION = 9
OP_HELLO = 10
OP_HEARTBEAT_ACK = 11

# Intents: GUILDS | GUILD_MEMBERS | GUILD_MESSAGES | MESSAGE_CONTENT
DEFAULT_INTENTS = (1 << 0) | (1 << 1) | (1 << 9) | (1 << 15)


class DiscordGateway:
    """Discord Gateway WebSocket client handling the HELLO -> IDENTIFY -> READY flow."""

    def __init__(self, bot_token: str) -> None:
        self._token = bot_token
        self._ws: ClientConnection | None = None
        self._heartbeat_interval: float = 41.25
        self._last_sequence: int | None = None
        self._session_id: str | None = None
        self._resume_url: str | None = None
        self._running = False
        self._event_callback: Callable[[dict], Awaitable[None]] | None = None
        self._user_id: str | None = None
        self._heartbeat_task: asyncio.Task | None = None
        self._last_heartbeat_ack = True

    def set_event_callback(self, callback: Callable[[dict], Awaitable[None]]) -> None:
        """Register an async callback invoked for every DISPATCH event."""
        self._event_callback = callback

    async def connect(self) -> None:
        """Connect to the Discord Gateway with automatic reconnect."""
        try:
            from websockets.asyncio.client import connect as ws_connect
            from websockets.exceptions import ConnectionClosed
        except ImportError:
            log.warning("websockets_not_available")
            return

        self._running = True
        while self._running:
            url = self._resume_url if self._resume_url else GATEWAY_URL
            try:
                async with ws_connect(url) as ws:
                    self._ws = ws
                    await self._receive_loop(ws)
            except ConnectionClosed as exc:
                if not self._running:
                    break
                log.warning(
                    "gateway_connection_closed",
                    code=exc.code,
                    reason=exc.reason,
                )
                # Clear resume state on hard closes
                if exc.code in (4004, 4010, 4011, 4012, 4013, 4014):
                    self._session_id = None
                    self._resume_url = None
                    self._running = False
                    break
                await asyncio.sleep(2)
            except Exception as exc:
                if not self._running:
                    break
                log.warning("gateway_disconnected", error=str(exc))
                await asyncio.sleep(5)
            finally:
                self._ws = None
                self._cancel_heartbeat()

        log.info("gateway_stopped")

    async def _receive_loop(self, ws) -> None:
        """Main receive loop processing all gateway opcodes."""
        async for raw_message in ws:
            if not self._running:
                break

            data = json.loads(raw_message)
            op = data.get("op")
            seq = data.get("s")
            if seq is not None:
                self._last_sequence = seq

            if op == OP_HELLO:
                await self._handle_hello(ws, data)
            elif op == OP_HEARTBEAT_ACK:
                self._last_heartbeat_ack = True
            elif op == OP_RECONNECT:
                log.info("gateway_reconnect_requested")
                await self.disconnect()
                return
            elif op == OP_INVALID_SESSION:
                can_resume = data.get("d", False)
                log.warning("gateway_invalid_session", can_resume=can_resume)
                await asyncio.sleep(3)
                if can_resume and self._session_id:
                    await self._resume(ws)
                else:
                    self._session_id = None
                    self._resume_url = None
                    await self._identify(ws)
            elif op == OP_DISPATCH:
                await self._handle_dispatch(data)

    async def _handle_hello(self, ws, data: dict) -> None:
        """Handle HELLO: start heartbeating then identify or resume."""
        self._heartbeat_interval = data["d"]["heartbeat_interval"] / 1000.0
        self._cancel_heartbeat()
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop(ws))

        if self._session_id and self._resume_url:
            await self._resume(ws)
        else:
            await self._identify(ws)

    async def _handle_dispatch(self, data: dict) -> None:
        """Handle DISPATCH events and update session state."""
        event_type = data.get("t")
        event_data = data.get("d", {})

        log.info(
            "gateway_dispatch", event_type=event_type, has_callback=self._event_callback is not None
        )

        if event_type == "READY":
            self._session_id = event_data.get("session_id")
            self._resume_url = event_data.get("resume_gateway_url")
            self._user_id = event_data.get("user", {}).get("id")
            log.info(
                "gateway_ready",
                user_id=self._user_id,
                session_id=self._session_id,
            )
        elif event_type == "RESUMED":
            log.info("gateway_resumed", session_id=self._session_id)

        if self._event_callback:
            try:
                await self._event_callback({"event_type": event_type, **event_data})
            except Exception as exc:
                log.error("event_callback_error", error=str(exc))

    async def _identify(self, ws) -> None:
        """Send IDENTIFY payload."""
        payload = {
            "op": OP_IDENTIFY,
            "d": {
                "token": self._token,
                "intents": DEFAULT_INTENTS,
                "properties": {
                    "os": "linux",
                    "browser": "discord_mcp",
                    "device": "discord_mcp",
                },
            },
        }
        await ws.send(json.dumps(payload))
        log.debug("gateway_identify_sent")

    async def _resume(self, ws) -> None:
        """Send RESUME payload to replay missed events."""
        payload = {
            "op": OP_RESUME,
            "d": {
                "token": self._token,
                "session_id": self._session_id,
                "seq": self._last_sequence,
            },
        }
        await ws.send(json.dumps(payload))
        log.debug("gateway_resume_sent", session_id=self._session_id, seq=self._last_sequence)

    async def _heartbeat_loop(self, ws) -> None:
        """Send heartbeats at the interval specified by HELLO."""
        self._last_heartbeat_ack = True
        while self._running:
            payload = {"op": OP_HEARTBEAT, "d": self._last_sequence}
            try:
                await ws.send(json.dumps(payload))
            except Exception:
                break

            await asyncio.sleep(self._heartbeat_interval)

            if not self._last_heartbeat_ack:
                log.warning("gateway_heartbeat_timeout")
                # Zombie connection — force reconnect
                try:
                    await ws.close(code=4000, reason="heartbeat timeout")
                except Exception:
                    pass
                break

            self._last_heartbeat_ack = False

    def _cancel_heartbeat(self) -> None:
        if self._heartbeat_task is not None:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None

    async def listen(self, event_callback: Callable[[dict], Awaitable[None]] | None = None) -> None:
        """Convenience entrypoint: set optional callback then connect."""
        if event_callback:
            self._event_callback = event_callback
        await self.connect()

    async def disconnect(self) -> None:
        """Gracefully disconnect from the gateway."""
        self._running = False
        self._cancel_heartbeat()
        if self._ws:
            try:
                await self._ws.close(code=1000, reason="client disconnect")
            except Exception:
                pass
            self._ws = None
        log.info("gateway_disconnected")

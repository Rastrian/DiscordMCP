# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from discord_mcp_platform.errors import AuthenticationError
from discord_mcp_platform.control_plane.mcp_clients import MCPClientService


class MCPAuth:
    def __init__(self, client_service: MCPClientService) -> None:
        self._client_service = client_service

    async def authenticate(self, token: str) -> dict:
        from discord_mcp_platform.security.secrets import hash_token

        token_hash = hash_token(token)
        client = await self._client_service.validate_client(token_hash)
        if client is None:
            raise AuthenticationError("invalid MCP client token")
        if not client.get("active", True):
            raise AuthenticationError("MCP client is deactivated")
        return client

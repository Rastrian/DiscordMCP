# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from discord_mcp_platform.db.models import MCPClient
from discord_mcp_platform.security.secrets import generate_token, hash_token


def _client_to_dict(client: MCPClient) -> dict:
    return {
        "id": client.id,
        "workspace_id": client.workspace_id,
        "name": client.name,
        "scopes": client.scopes,
        "active": client.active,
        "created_at": client.created_at.isoformat() if client.created_at else None,
    }


class MCPClientService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_client(
        self,
        workspace_id: str,
        name: str,
        scopes: str,
    ) -> tuple[str, str]:
        raw_token = generate_token()
        token_hash = hash_token(raw_token)
        client = MCPClient(
            workspace_id=workspace_id,
            name=name,
            token_hash=token_hash,
            scopes=scopes,
        )
        self._session.add(client)
        await self._session.flush()
        return client.id, raw_token

    async def validate_client(self, token_hash: str) -> dict | None:
        stmt = select(MCPClient).where(
            MCPClient.token_hash == token_hash,
            MCPClient.active.is_(True),
        )
        result = await self._session.execute(stmt)
        client = result.scalar_one_or_none()
        if client is None:
            return None
        return _client_to_dict(client)

    async def list_clients(self, workspace_id: str) -> list[dict]:
        stmt = select(MCPClient).where(
            MCPClient.workspace_id == workspace_id,
            MCPClient.active.is_(True),
        )
        result = await self._session.execute(stmt)
        clients = result.scalars().all()
        return [_client_to_dict(c) for c in clients]

    async def revoke_client(self, client_id: str) -> bool:
        stmt = (
            update(MCPClient)
            .where(MCPClient.id == client_id, MCPClient.active.is_(True))
            .values(active=False)
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0

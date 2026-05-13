# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from discord_mcp_platform.db.models import GuildPolicy


def _policy_to_dict(policy: GuildPolicy) -> dict:
    return {
        "id": policy.id,
        "workspace_id": policy.workspace_id,
        "guild_id": policy.guild_id,
        "permission_flags": policy.permission_flags,
        "role": policy.role,
        "created_at": policy.created_at.isoformat() if policy.created_at else None,
        "updated_at": policy.updated_at.isoformat() if policy.updated_at else None,
    }


class GuildPolicyService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def set_policy(
        self,
        workspace_id: str,
        guild_id: str,
        permission_flags: str,
        role: str,
    ) -> dict:
        stmt = select(GuildPolicy).where(
            GuildPolicy.workspace_id == workspace_id,
            GuildPolicy.guild_id == guild_id,
        )
        result = await self._session.execute(stmt)
        policy = result.scalar_one_or_none()

        if policy is None:
            policy = GuildPolicy(
                workspace_id=workspace_id,
                guild_id=guild_id,
                permission_flags=permission_flags,
                role=role,
            )
            self._session.add(policy)
        else:
            policy.permission_flags = permission_flags
            policy.role = role

        await self._session.flush()
        return _policy_to_dict(policy)

    async def get_policy(self, workspace_id: str, guild_id: str) -> dict | None:
        stmt = select(GuildPolicy).where(
            GuildPolicy.workspace_id == workspace_id,
            GuildPolicy.guild_id == guild_id,
        )
        result = await self._session.execute(stmt)
        policy = result.scalar_one_or_none()
        if policy is None:
            return None
        return _policy_to_dict(policy)

    async def list_policies(self, workspace_id: str) -> list[dict]:
        stmt = select(GuildPolicy).where(GuildPolicy.workspace_id == workspace_id)
        result = await self._session.execute(stmt)
        policies = result.scalars().all()
        return [_policy_to_dict(p) for p in policies]

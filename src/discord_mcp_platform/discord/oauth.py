# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

import hmac
import secrets
from urllib.parse import urlencode

import httpx

DISCORD_API_BASE = "https://discord.com/api/v10"
OAUTH_BASE = "https://discord.com/api/v10/oauth2/"


class DiscordOAuth:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri

    def get_authorize_url(self, state: str) -> str:
        params = {
            "client_id": self._client_id,
            "redirect_uri": self._redirect_uri,
            "response_type": "code",
            "scope": "identify guilds",
            "state": state,
        }
        return f"https://discord.com/api/v10/oauth2/authorize?{urlencode(params)}"

    async def exchange_code(self, code: str) -> dict:
        async with httpx.AsyncClient(base_url=DISCORD_API_BASE) as client:
            response = await client.post(
                "/oauth2/token",
                data={
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self._redirect_uri,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            return response.json()

    async def fetch_user_profile(self, access_token: str) -> dict:
        async with httpx.AsyncClient(base_url=DISCORD_API_BASE) as client:
            response = await client.get(
                "/users/@me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            return response.json()

    def generate_state(self) -> str:
        return secrets.token_urlsafe(32)

    def validate_state(self, state: str, expected: str) -> bool:
        return hmac.compare_digest(state, expected)

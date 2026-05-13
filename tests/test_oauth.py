# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from discord_mcp_platform.discord.oauth import DiscordOAuth


def test_generate_state():
    oauth = DiscordOAuth("id", "secret", "http://localhost/callback")
    state = oauth.generate_state()
    assert isinstance(state, str)
    assert len(state) > 10


def test_validate_state_success():
    oauth = DiscordOAuth("id", "secret", "http://localhost/callback")
    state = oauth.generate_state()
    assert oauth.validate_state(state, state) is True


def test_validate_state_failure():
    oauth = DiscordOAuth("id", "secret", "http://localhost/callback")
    assert oauth.validate_state("wrong", "expected") is False


def test_authorize_url():
    oauth = DiscordOAuth("my-client-id", "secret", "http://localhost/callback")
    url = oauth.get_authorize_url("test-state")
    assert "my-client-id" in url
    assert "test-state" in url
    assert "identify" in url
    assert "guilds" in url

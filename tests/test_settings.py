# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

import os

from discord_mcp_platform.app.settings import Settings


def test_settings_defaults():
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith(("MCP_", "APP_", "DEBUG", "API_", "DISCORD_", "AGENT_"))
    }
    s = Settings(_env_file=None, **{k: v for k, v in env.items() if k in Settings.model_fields})
    assert s.app_name == "discord-mcp-platform"
    assert s.debug is False
    assert s.api_port == 8000
    assert s.mcp_transport == "stdio"


def test_settings_custom():
    s = Settings(
        _env_file=None,
        app_name="test-app",
        debug=True,
        api_port=9000,
    )
    assert s.app_name == "test-app"
    assert s.debug is True
    assert s.api_port == 9000

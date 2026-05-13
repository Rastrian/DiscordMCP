# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from mcp.types import Resource


def get_resources() -> list[Resource]:
    return [
        Resource(
            uri="discord://automations/{guild_id}",
            name="Discord Automations",
            mimeType="application/json",
        ),
    ]

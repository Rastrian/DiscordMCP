# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MCPContext:
    workspace_id: str
    user_id: str | None = None
    mcp_client_id: str | None = None
    scopes: str = ""

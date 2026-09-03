# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

"""Single source of truth for the package version.

pyproject.toml declares ``dynamic = ["version"]`` and hatchling reads this
file via ``[tool.hatch.version]``, so the version lives in exactly one place.
Bump it here, run ``uv lock``, commit, then tag ``v<version>``.
"""

from __future__ import annotations

__version__ = "0.1.0"

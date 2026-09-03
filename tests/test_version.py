# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

"""Tests for single-source version metadata."""

from __future__ import annotations

import re

from discord_mcp_platform._version import __version__
from discord_mcp_platform.app.main import app


def test_version_is_semver():
    assert re.fullmatch(r"\d+\.\d+\.\d+", __version__), (
        f"__version__ {__version__!r} must match MAJOR.MINOR.PATCH"
    )


def test_fastapi_app_reports_package_version():
    assert app.version == __version__

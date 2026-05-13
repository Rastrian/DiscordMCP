# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

import pytest

from discord_mcp_platform.discord.snowflake import validate_snowflake


def test_valid_snowflake():
    assert validate_snowflake("123456789012345678") == "123456789012345678"


def test_short_snowflake():
    assert validate_snowflake("123456789012345") == "123456789012345"


def test_long_snowflake():
    assert validate_snowflake("1234567890123456789012345") == "1234567890123456789012345"


def test_invalid_snowflake_letters():
    with pytest.raises(ValueError, match="invalid Discord snowflake"):
        validate_snowflake("abc123456789012345")


def test_invalid_snowflake_too_short():
    with pytest.raises(ValueError):
        validate_snowflake("12345")


def test_invalid_snowflake_too_long():
    with pytest.raises(ValueError):
        validate_snowflake("12345678901234567890123456")


def test_invalid_snowflake_empty():
    with pytest.raises(ValueError):
        validate_snowflake("")

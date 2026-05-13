# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

import re

from discord_mcp_platform.errors import ValidationError

_SNOWFLAKE_RE = re.compile(r"^[0-9]{15,25}$")


def validate_message_content(content: str, allow_everyone: bool = False) -> str:
    if not content:
        raise ValidationError("message content must not be empty")
    if not allow_everyone:
        if "@everyone" in content or "@here" in content:
            raise ValidationError("message content must not contain @everyone or @here")
    if len(content) > 2000:
        raise ValidationError("message content must not exceed 2000 characters")
    return content


def validate_channel_name(name: str) -> str:
    cleaned = name.strip().lower().replace(" ", "-")
    if not cleaned:
        raise ValidationError("channel name must not be empty")
    if len(cleaned) > 100:
        raise ValidationError("channel name must not exceed 100 characters")
    return cleaned


def validate_snowflake(value: str) -> str:
    if not _SNOWFLAKE_RE.match(value):
        raise ValidationError(f"invalid Discord snowflake: {value!r}")
    return value

# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

import re

SENSITIVE_KEYS: frozenset[str] = frozenset(
    {
        "token",
        "access_token",
        "refresh_token",
        "secret",
        "password",
        "authorization",
        "cookie",
    }
)

_REDACTED = "***REDACTED***"

_BOT_TOKEN_RE = re.compile(r"Bot [A-Za-z0-9._-]+")
_BEARER_TOKEN_RE = re.compile(r"Bearer [A-Za-z0-9._-]+")
_DEFAULT_PATTERNS = [_BOT_TOKEN_RE, _BEARER_TOKEN_RE]


def redact_dict(data: dict) -> dict:
    result: dict = {}
    for key, value in data.items():
        if key in SENSITIVE_KEYS:
            result[key] = _REDACTED
        elif isinstance(value, dict):
            result[key] = redact_dict(value)
        elif isinstance(value, list):
            result[key] = [redact_dict(item) if isinstance(item, dict) else item for item in value]
        else:
            result[key] = value
    return result


def redact_string(text: str, patterns: list[str] | None = None) -> str:
    compiled = _DEFAULT_PATTERNS
    if patterns is not None:
        compiled = [re.compile(p) for p in patterns]
    result = text
    for pat in compiled:
        result = pat.sub("[REDACTED]", result)
    return result

# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from discord_mcp_platform.security.redaction import redact_dict, redact_string


def test_redact_dict_masks_tokens():
    data = {
        "access_token": "secret123",
        "name": "visible",
        "nested": {"token": "hidden", "ok": True},
    }
    result = redact_dict(data)
    assert result["access_token"] == "***REDACTED***"
    assert result["name"] == "visible"
    assert result["nested"]["token"] == "***REDACTED***"
    assert result["nested"]["ok"] is True


def test_redact_dict_handles_empty():
    assert redact_dict({}) == {}


def test_redact_string_bot_token():
    result = redact_string("Authorization: Bot abcdefg.hijklmnop.qrstuv")
    assert "Bot" not in result
    assert "[REDACTED]" in result


def test_redact_string_bearer_token():
    result = redact_string("Bearer mytoken123")
    assert "mytoken123" not in result
    assert "[REDACTED]" in result


def test_redact_string_no_tokens():
    text = "Hello world"
    assert redact_string(text) == text

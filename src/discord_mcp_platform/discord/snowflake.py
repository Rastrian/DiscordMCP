# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

import re

SNOWFLAKE_RE = re.compile(r"^[0-9]{15,25}$")


def validate_snowflake(value: str) -> str:
    if not SNOWFLAKE_RE.match(value):
        raise ValueError(f"invalid Discord snowflake: {value!r}")
    return value

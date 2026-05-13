# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass


class Base(MappedAsDataclass, DeclarativeBase):
    pass


target_metadata = Base.metadata

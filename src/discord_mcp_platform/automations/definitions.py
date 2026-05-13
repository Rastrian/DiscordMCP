# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from enum import StrEnum


class TriggerType(StrEnum):
    MESSAGE_CREATED = "message_created"
    MEMBER_JOINED = "member_joined"
    REACTION_ADDED = "reaction_added"
    SCHEDULED = "scheduled"
    MANUAL = "manual"


class ActionType(StrEnum):
    SEND_MESSAGE = "send_message"
    DELETE_MESSAGE = "delete_message"
    ADD_ROLE = "add_role"
    REMOVE_ROLE = "remove_role"
    CREATE_THREAD = "create_thread"
    NOTIFY = "notify"
    DRAFT = "draft"

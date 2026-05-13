"""initial_schema

Revision ID: 0001_initial
Revises: None
Create Date: 2026-05-12 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("discord_user_id", sa.String(), nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=True),
        sa.Column("avatar_url", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_discord_user_id", "users", ["discord_user_id"], unique=True)

    # --- workspaces ---
    op.create_table(
        "workspaces",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("owner_user_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_workspaces_slug", "workspaces", ["slug"], unique=True)

    # --- oauth_accounts ---
    op.create_table(
        "oauth_accounts",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("access_token", sa.String(), nullable=False),
        sa.Column("refresh_token", sa.String(), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(), nullable=True),
        sa.Column("scopes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- workspace_memberships ---
    op.create_table(
        "workspace_memberships",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id", "user_id", name="uq_workspace_user"),
    )

    # --- guild_installations ---
    op.create_table(
        "guild_installations",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("guild_id", sa.String(), nullable=False),
        sa.Column("bot_installed", sa.Boolean(), nullable=True),
        sa.Column("installed_by_user_id", sa.String(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["installed_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_guild_installations_guild_id", "guild_installations", ["guild_id"])

    # --- mcp_clients ---
    op.create_table(
        "mcp_clients",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("scopes", sa.String(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- policies ---
    op.create_table(
        "policies",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("guild_id", sa.String(), nullable=True),
        sa.Column("channel_id", sa.String(), nullable=True),
        sa.Column("permission_flags", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- guild_policies ---
    op.create_table(
        "guild_policies",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("guild_id", sa.String(), nullable=False),
        sa.Column("permission_flags", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_guild_policies_guild_id", "guild_policies", ["guild_id"])

    # --- channel_policies ---
    op.create_table(
        "channel_policies",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("guild_id", sa.String(), nullable=False),
        sa.Column("channel_id", sa.String(), nullable=False),
        sa.Column("permission_flags", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_channel_policies_channel_id", "channel_policies", ["channel_id"])

    # --- audit_events ---
    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("mcp_client_id", sa.String(), nullable=True),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("guild_id", sa.String(), nullable=True),
        sa.Column("channel_id", sa.String(), nullable=True),
        sa.Column("target_id", sa.String(), nullable=True),
        sa.Column("details", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- automations ---
    op.create_table(
        "automations",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("guild_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("trigger_type", sa.String(), nullable=False),
        sa.Column("trigger_config", sa.String(), nullable=False),
        sa.Column("action_type", sa.String(), nullable=False),
        sa.Column("action_config", sa.String(), nullable=False),
        sa.Column("target_channel_ids", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- bot_configs ---
    op.create_table(
        "bot_configs",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("workspace_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("bot_token_hash", sa.String(128), nullable=True),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bot_configs_workspace_id", "bot_configs", ["workspace_id"])


def downgrade() -> None:
    op.drop_table("bot_configs")
    op.drop_table("automations")
    op.drop_table("audit_events")
    op.drop_table("channel_policies")
    op.drop_table("guild_policies")
    op.drop_table("policies")
    op.drop_table("mcp_clients")
    op.drop_table("guild_installations")
    op.drop_table("workspace_memberships")
    op.drop_table("oauth_accounts")
    op.drop_table("workspaces")
    op.drop_table("users")

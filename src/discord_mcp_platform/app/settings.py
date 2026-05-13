# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # App
    app_name: str = "discord-mcp-platform"
    debug: bool = False
    log_level: str = "INFO"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Database
    database_url: str = "postgresql+psycopg://postgres:postgres@db:5432/discord_mcp_platform"
    database_echo: bool = False

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # Discord OAuth
    discord_client_id: str = ""
    discord_client_secret: str = ""
    discord_redirect_uri: str = "http://localhost:8000/auth/discord/callback"
    discord_bot_token: str = ""

    # Security
    secret_key: str = "change-me-in-production"
    allowed_guild_ids: list[str] = []
    allowed_channel_ids: list[str] = []

    # MCP
    mcp_transport: str = "stdio"  # "stdio" | "http"

    # Gateway
    enable_gateway: bool = False  # Enable Discord Gateway WebSocket for real-time events

    # Agent (Conversational AI)
    agent_enabled: bool = False
    agent_api_base_url: str = "https://api.z.ai/api/anthropic"
    agent_api_key: str = ""
    agent_model: str = "glm-4-plus"
    agent_system_prompt: str = (
        "You are a helpful Discord bot assistant. "
        "Be concise and friendly. Keep responses under 1500 characters."
    )
    agent_max_history: int = 20
    agent_cooldown_seconds: int = 5


settings = Settings()

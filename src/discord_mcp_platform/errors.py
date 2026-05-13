# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.


class AppError(Exception):
    """Base application error."""


class AuthenticationError(AppError):
    """Request could not be authenticated."""


class AuthorizationError(AppError):
    """Authenticated principal lacks required permissions."""


class PolicyDeniedError(AuthorizationError):
    """Action denied by platform policy."""


class DiscordPermissionError(AppError):
    """Discord bot lacks required guild/channel permissions."""


class DiscordNotFoundError(AppError):
    """Requested Discord resource does not exist."""


class RateLimitError(AppError):
    """Rate limit exceeded."""

    def __init__(self, retry_after: float | None = None) -> None:
        self.retry_after = retry_after
        super().__init__(f"rate limited, retry_after={retry_after}")


class ExternalServiceError(AppError):
    """Upstream service call failed."""


class ValidationError(AppError):
    """Input validation failed."""

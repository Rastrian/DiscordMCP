# Security Policy

## Strict Non-Goals

- No self-bot behavior. No user tokens. No browser automation of Discord.
- The platform never sends messages as a personal Discord user, never reads
  user DMs by impersonation, and never bypasses Discord permissions, rate
  limits, OAuth scopes, gateway restrictions, or API limits.
- No spam, raid, mass-DM, invite-spam, reaction-spam, or stealth-monitoring
  tooling.

All Discord automation executes through authorized Discord bot accounts or
official webhooks, via OAuth2/application flows only.

## Authorization Model

Every request passes multiple gates, in order:

```text
MCP client auth
  -> platform user/session auth
  -> workspace membership check
  -> guild installation check
  -> platform role/permission check
  -> channel policy check
  -> Discord bot permission check
  -> rate-limit check
  -> execution
  -> audit log
```

Discord permissions answer "can the bot do this?"; platform permissions
answer "should this user be allowed to make the bot do this?" — both must
pass.

Implementation notes (verified behavior):

- The Discord-side permission check is **fail-closed**: if the check itself
  cannot be computed (API error, missing intents), the operation is denied
  (`check_discord_permission`, `src/discord_mcp_platform/discord/permissions.py`).
- Permission bit constants are verified against the official Discord
  permissions table by a regression test (`tests/test_permissions.py`).

## Dangerous Operation Policy

State-changing operations default to `dry_run=true` and require an explicit
`confirmation` to execute. The authoritative list lives in
`DANGEROUS_OPERATIONS` (`src/discord_mcp_platform/security/policy.py`):
message send/edit/delete/bulk-delete, channel create/edit/delete and
permission changes, role create/modify/delete/assign/remove/reorder, member
kick/ban/unban/timeout, webhook create/modify/delete/execute, guild modify
and incident actions, invites create/delete, automod create/update/delete,
event create/update/delete, pins add/remove, thread create,
reaction add/remove/remove-user, automation changes.

Every executed write is recorded in the audit log with the acting MCP
client, guild, channel and target.

## Known limitations

- Channel permission overwrites (allow/deny per role or user) are not yet
  resolved when computing the bot's effective permissions — the check uses
  guild-level role permissions only. Overwrite-aware resolution is a
  planned follow-up.

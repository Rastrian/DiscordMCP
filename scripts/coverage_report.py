#!/usr/bin/env python3
"""Discord OpenAPI coverage report.

Compares the vendored Discord OpenAPI spec (specs/openapi.json) against the
REST endpoints implemented in DiscordRestClient and the tools exposed by the
MCP server, then writes specs/COVERAGE.md.

Usage:
    python3 scripts/coverage_report.py             # write specs/COVERAGE.md
    python3 scripts/coverage_report.py --check     # anti-regression guard (exit 1 on regression)
    python3 scripts/coverage_report.py --summary   # print a markdown summary to stdout only

Pure standard library -- no external dependencies.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = REPO_ROOT / "specs" / "openapi.json"
COVERAGE_PATH = REPO_ROOT / "specs" / "COVERAGE.md"
BASELINE_PATH = REPO_ROOT / "specs" / ".coverage-baseline"
REST_CLIENT_PATH = REPO_ROOT / "src" / "discord_mcp_platform" / "discord" / "rest_client.py"
TOOLS_DIR = REPO_ROOT / "src" / "discord_mcp_platform" / "mcp" / "tools"

HTTP_METHODS = ("get", "post", "put", "patch", "delete")

REST_CALL_RE = re.compile(r'self\._request\(\s*"([A-Z]+)",\s*f?"([^"]+)"')
MCP_TOOL_RE = re.compile(r'name="(discord\.[a-z_.]+)"')
PATH_PARAM_RE = re.compile(r"\{[^{}]*\}")

# Endpoint groups explicitly declared out of scope for this product.
OUT_OF_SCOPE_RULES: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (label, re.compile(pattern))
    for label, pattern in (
        ("oauth2", r"^/oauth2/"),
        ("application-commands (global)", r"^/applications/\{[^}]+\}/commands"),
        ("partner-sdk", r"/partner-sdk"),
        ("lobbies", r"^/lobbies"),
        ("soundboard", r"soundboard"),
        ("users/@me/connections", r"^/users/@me/connections"),
        ("skus", r"^/skus/"),
        ("store", r"/store"),
        ("entitlements", r"entitlements"),
        ("role-connections", r"role-connection"),
        ("activity-instances", r"activity-instance"),
        ("gateway", r"^/gateway"),
        ("sticker-packs", r"^/sticker-packs"),
        ("invite target-users job-status", r"/target-users/job-status"),
    )
)

# Product scope groups, ordered so that the first matching rule wins:
# guild/channel/message/member/role/thread/webhook/invite/moderation/events/
# automod/emoji/sticker/voice-state/incident/onboarding/welcome-screen/widget/
# pins/reactions/guild application-commands/interactions.
GROUP_RULES: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (group, re.compile(pattern))
    for group, pattern in (
        ("incident", r"/incident-actions"),
        ("automod", r"/auto-moderation/"),
        ("events", r"/scheduled-events"),
        ("onboarding", r"/onboarding|/new-member-welcome"),
        ("welcome-screen", r"/welcome-screen"),
        ("widget", r"/widget"),
        ("emoji", r"^/guilds/\{[^}]+\}/emojis"),
        ("sticker", r"^/guilds/\{[^}]+\}/stickers|^/stickers/\{"),
        ("voice-state", r"/voice-states/"),
        (
            "application-commands",
            r"^/applications/\{[^}]+\}/guilds/\{[^}]+\}/commands",
        ),
        ("interactions", r"^/interactions/"),
        ("invite", r"/invites"),
        ("webhook", r"/webhooks"),
        ("thread", r"/threads|/thread-members"),
        ("reactions", r"/reactions"),
        ("pins", r"/pins"),
        ("message", r"/messages"),
        ("moderation", r"/bans|/bulk-ban|/audit-logs|/prune"),
        ("role", r"/roles"),
        ("member", r"/members|^/users/@me/guilds"),
        (
            "channel",
            r"^/channels/\{[^}]+\}$"
            r"|^/channels/\{[^}]+\}/(followers|permissions|typing)",
        ),
        ("channel", r"^/guilds/\{[^}]+\}/channels"),
        (
            "guild",
            r"^/guilds/\{[^}]+\}$|^/guilds/\{[^}]+\}/(preview|regions|vanity-url)$",
        ),
    )
)

GROUP_ORDER = (
    "guild",
    "channel",
    "message",
    "pins",
    "reactions",
    "thread",
    "member",
    "role",
    "moderation",
    "automod",
    "events",
    "emoji",
    "sticker",
    "voice-state",
    "incident",
    "onboarding",
    "welcome-screen",
    "widget",
    "webhook",
    "invite",
    "application-commands",
    "interactions",
)

# MCP tool name prefix (discord.<prefix>.*) -> scope group. None means the tool
# is platform-only and is not backed by a Discord REST endpoint: audit.list
# reads the platform audit_events table (AuditService), and automation.draft
# is a pure platform tool.
TOOL_GROUP_BY_PREFIX = {
    "guild": "guild",
    "channel": "channel",
    "pin": "pins",
    "message": "message",
    "member": "member",
    "role": "role",
    "thread": "thread",
    "webhook": "webhook",
    "invite": "invite",
    "reaction": "reactions",
    "event": "events",
    "automod": "automod",
    "audit": None,
    "automation": None,
}


def normalize_path(path: str) -> str:
    """Collapse `{param}` and `{variable}` placeholders into `{}`."""
    return PATH_PARAM_RE.sub("{}", path)


def classify_path(path: str) -> tuple[str, str | None]:
    """Return ("in", group) / ("out", label) / ("other", None) for a spec path."""
    for label, pattern in OUT_OF_SCOPE_RULES:
        if pattern.search(path):
            return ("out", label)
    for group, pattern in GROUP_RULES:
        if pattern.search(path):
            return ("in", group)
    return ("other", None)


def iter_spec_endpoints(spec: dict) -> Iterator[tuple[str, str]]:
    for path, path_item in spec.get("paths", {}).items():
        for method in path_item:
            if method.lower() in HTTP_METHODS:
                yield (method.upper(), path)


def load_rest_endpoints() -> set[tuple[str, str]]:
    """Extract unique (METHOD, normalized path) pairs from DiscordRestClient."""
    source = REST_CLIENT_PATH.read_text(encoding="utf-8")
    return {(method, normalize_path(path)) for method, path in REST_CALL_RE.findall(source)}


def load_mcp_tools() -> list[str]:
    tools: list[str] = []
    for path in sorted(TOOLS_DIR.glob("*.py")):
        tools.extend(MCP_TOOL_RE.findall(path.read_text(encoding="utf-8")))
    return sorted(set(tools))


def pct(part: int, whole: int) -> str:
    return f"{100.0 * part / whole:.1f}%" if whole else "n/a"


def build_report() -> dict:
    """Compute all coverage numbers and render the COVERAGE.md content."""
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))

    in_scope: dict[str, list[tuple[str, str]]] = {}
    out_of_scope: dict[str, int] = {}
    unclassified: list[tuple[str, str]] = []
    spec_lookup: dict[tuple[str, str], tuple[str, str | None]] = {}

    for method, path in sorted(iter_spec_endpoints(spec)):
        kind, name = classify_path(path)
        key = (method, normalize_path(path))
        if kind == "in":
            in_scope.setdefault(name, []).append((method, path))
        elif kind == "out":
            out_of_scope[name] = out_of_scope.get(name, 0) + 1
        else:
            unclassified.append((method, path))
        spec_lookup[key] = (kind, name)

    rest_endpoints = load_rest_endpoints()
    implemented_by_group: dict[str, set[tuple[str, str]]] = {}
    rest_outside: list[tuple[str, str, str]] = []
    for endpoint in sorted(rest_endpoints):
        kind, name = spec_lookup.get(endpoint, ("missing", None))
        if kind == "in":
            implemented_by_group.setdefault(name, set()).add(endpoint)
        elif kind == "out":
            rest_outside.append((*endpoint, f"out of scope: {name}"))
        elif kind == "other":
            rest_outside.append((*endpoint, "outside product scope"))
        else:
            rest_outside.append((*endpoint, "not found in spec"))

    mcp_tools = load_mcp_tools()
    tools_by_group: dict[str, int] = {group: 0 for group in GROUP_ORDER}
    platform_tools: list[str] = []
    unknown_tools: list[str] = []
    for tool in mcp_tools:
        prefix = tool.split(".")[1]
        group = TOOL_GROUP_BY_PREFIX.get(prefix, "?")
        if prefix not in TOOL_GROUP_BY_PREFIX:
            unknown_tools.append(tool)
        elif group is None:
            platform_tools.append(tool)
        else:
            tools_by_group[group] += 1

    total_spec_ops = sum(len(ops) for ops in in_scope.values()) + sum(out_of_scope.values())
    total_spec_ops += len(unclassified)
    total_in_scope = sum(len(ops) for ops in in_scope.values())
    total_implemented = sum(len(ops) for ops in implemented_by_group.values())

    lines: list[str] = []
    lines.append("# Discord API Coverage Report")
    lines.append("")
    lines.append("> Generated by `scripts/coverage_report.py` — do not edit by hand.")
    lines.append(
        "> Source of truth: [`specs/openapi.json`](openapi.json), vendored from the official"
        " [discord/discord-api-spec](https://github.com/discord/discord-api-spec)."
    )
    lines.append("")
    lines.append(
        f"- **Generated (UTC):** {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}"
    )
    lines.append(
        f"- **Spec version:** {spec.get('info', {}).get('version', '?')}"
        f" (OpenAPI {spec.get('openapi', '?')})"
    )
    lines.append(f"- **Spec operations:** {total_spec_ops} (`METHOD /path` pairs)")
    lines.append("")
    lines.append("## Totals")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---:|")
    lines.append(f"| Spec operations (total) | {total_spec_ops} |")
    explicit_out = sum(out_of_scope.values())
    lines.append(f"| Out of scope (explicit groups) | {explicit_out} |")
    lines.append(f"| Outside product scope (unclassified) | {len(unclassified)} |")
    lines.append(f"| **Spec operations in scope** | **{total_in_scope}** |")
    lines.append(f"| **Implemented in REST client (in scope)** | **{total_implemented}** |")
    lines.append(f"| REST coverage (in scope) | {pct(total_implemented, total_in_scope)} |")
    lines.append(f"| MCP tools (spec-backed) | {len(mcp_tools) - len(platform_tools)} |")
    lines.append(f"| MCP tools (platform-only) | {len(platform_tools)} |")
    lines.append("")
    lines.append("## Coverage by group")
    lines.append("")
    lines.append("| Group | Spec (in scope) | REST implemented | MCP tools | % REST | Missing |")
    lines.append("|---|---:|---:|---:|---:|---|")
    for group in GROUP_ORDER:
        spec_items = sorted(in_scope.get(group, []))
        implemented = implemented_by_group.get(group, set())
        missing = [
            f"`{method} {path}`"
            for method, path in spec_items
            if (method, normalize_path(path)) not in implemented
        ]
        lines.append(
            f"| {group} | {len(spec_items)} | {len(implemented)}"
            f" | {tools_by_group.get(group, 0)} | {pct(len(implemented), len(spec_items))}"
            f" | {'<br>'.join(missing) if missing else '—'} |"
        )
    lines.append(
        f"| **Total** | **{total_in_scope}** | **{total_implemented}**"
        f" | **{len(mcp_tools) - len(platform_tools)}**"
        f" | **{pct(total_implemented, total_in_scope)}** | |"
    )
    lines.append("")
    lines.append("## Out-of-scope groups (explicit)")
    lines.append("")
    lines.append("| Group | Operations |")
    lines.append("|---|---:|")
    for label in sorted(out_of_scope):
        lines.append(f"| {label} | {out_of_scope[label]} |")
    lines.append("")
    lines.append("## Spec operations outside the product scope (unclassified)")
    lines.append("")
    if unclassified:
        joined = ", ".join(f"`{method} {path}`" for method, path in unclassified)
        lines.append(joined)
    else:
        lines.append("_none_")
    lines.append("")
    lines.append("## REST client endpoints outside the in-scope spec surface")
    lines.append("")
    lines.append("These `DiscordRestClient` methods call Discord endpoints that are not part of")
    lines.append("the in-scope product surface:")
    lines.append("")
    lines.append("| Endpoint | Status |")
    lines.append("|---|---|")
    for method, path, reason in rest_outside:
        lines.append(f"| `{method} {path}` | {reason} |")
    if not rest_outside:
        lines.append("| _none_ | |")
    lines.append("")
    lines.append("## Regression guard")
    lines.append("")
    lines.append("`specs/.coverage-baseline` stores the current number of in-scope REST endpoints.")
    lines.append("`python3 scripts/coverage_report.py --check` exits with status 1 when the total")
    lines.append("drops below the baseline, and raises the baseline when coverage grows.")
    lines.append("")

    return {
        "total_spec_ops": total_spec_ops,
        "explicit_out": explicit_out,
        "unclassified": len(unclassified),
        "total_in_scope": total_in_scope,
        "total_implemented": total_implemented,
        "mcp_tools": len(mcp_tools),
        "platform_tools": len(platform_tools),
        "unknown_tools": unknown_tools,
        "rest_outside": len(rest_outside),
        "content": "\n".join(lines),
    }


def print_summary(report: dict) -> None:
    backed = report["mcp_tools"] - report["platform_tools"]
    print(
        f"**Spec**: {report['total_spec_ops']} operations"
        f" ({report['total_in_scope']} in scope,"
        f" {report['total_spec_ops'] - report['total_in_scope']} out of scope)"
    )
    print(
        f"**Implemented**: {report['total_implemented']}/{report['total_in_scope']}"
        f" in-scope REST endpoints"
        f" ({pct(report['total_implemented'], report['total_in_scope'])})"
    )
    print(f"**MCP tools**: {report['mcp_tools']} ({backed} backed by Discord REST endpoints)")


def ensure_baseline(total_implemented: int) -> None:
    if not BASELINE_PATH.exists():
        BASELINE_PATH.write_text(f"{total_implemented}\n", encoding="utf-8")
        print(f"baseline created: specs/.coverage-baseline = {total_implemented}")


def run_baseline_check(total_implemented: int) -> int:
    if not BASELINE_PATH.exists():
        BASELINE_PATH.write_text(f"{total_implemented}\n", encoding="utf-8")
        print(f"baseline created: specs/.coverage-baseline = {total_implemented}")
        return 0

    baseline = int(BASELINE_PATH.read_text(encoding="utf-8").strip())
    if total_implemented < baseline:
        print(
            f"coverage regression: {total_implemented} in-scope REST endpoints"
            f" < baseline {baseline}",
            file=sys.stderr,
        )
        print("Restore the removed endpoints or acknowledge the reduction by", file=sys.stderr)
        print("lowering specs/.coverage-baseline in an explicit commit.", file=sys.stderr)
        return 1
    if total_implemented > baseline:
        BASELINE_PATH.write_text(f"{total_implemented}\n", encoding="utf-8")
        print(f"baseline raised: {baseline} -> {total_implemented}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Discord OpenAPI coverage report.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check", action="store_true", help="guard against coverage regressions (exit 1)"
    )
    mode.add_argument(
        "--summary", action="store_true", help="print a markdown summary to stdout only"
    )
    args = parser.parse_args()

    if not SPEC_PATH.exists():
        print(f"spec not found: {SPEC_PATH}", file=sys.stderr)
        print("run scripts/fetch-discord-spec.sh first", file=sys.stderr)
        return 2

    report = build_report()

    if report["unknown_tools"]:
        for tool in report["unknown_tools"]:
            print(f"warning: tool {tool} has no group mapping", file=sys.stderr)

    if args.summary:
        print_summary(report)
        return 0

    COVERAGE_PATH.write_text(report["content"], encoding="utf-8")
    print(f"wrote {COVERAGE_PATH}")
    print_summary(report)

    if args.check:
        return run_baseline_check(report["total_implemented"])

    ensure_baseline(report["total_implemented"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Deterministic routing helpers for non-gpt-subagent-worker scripts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


VALID_PROVIDERS = {"ollama", "lmstudio", "deepseek"}
VALID_SANDBOXES = {"read-only", "workspace-write"}
PROVIDER_ALIASES = {
    "ollama": "ollama",
    "lmstudio": "lmstudio",
    "lm-studio": "lmstudio",
    "lm studio": "lmstudio",
    "deepseek": "deepseek",
}


class RoutingError(ValueError):
    """Raised when worker routing input is invalid."""


@dataclass(frozen=True)
class WorkerSpec:
    provider: str
    model: str
    cwd: str
    sandbox: str
    output: str


def normalize_provider(provider: str) -> str:
    key = provider.strip().lower()
    normalized = PROVIDER_ALIASES.get(key)
    if normalized is None:
        raise RoutingError(f"unknown provider: {provider}")
    return normalized


def validate_sandbox(sandbox: str) -> str:
    value = sandbox.strip()
    if value not in VALID_SANDBOXES:
        raise RoutingError(f"unsupported sandbox: {sandbox}")
    return value


def validate_spec(provider: str, model: str, cwd: str, sandbox: str, output: str) -> WorkerSpec:
    normalized_provider = normalize_provider(provider)
    if not model.strip():
        raise RoutingError("model is required")
    cwd_path = Path(cwd).expanduser()
    if not cwd_path.is_absolute():
        raise RoutingError("cwd must be an absolute path")
    if not output.strip():
        raise RoutingError("output path is required")
    return WorkerSpec(
        provider=normalized_provider,
        model=model.strip(),
        cwd=str(cwd_path),
        sandbox=validate_sandbox(sandbox),
        output=output,
    )


def codex_exec_command(spec: WorkerSpec) -> list[str]:
    if spec.provider not in {"ollama", "lmstudio"}:
        raise RoutingError(f"codex exec is not used for provider: {spec.provider}")
    return [
        "codex",
        "exec",
        "--oss",
        "--local-provider",
        spec.provider,
        "-m",
        spec.model,
        "-C",
        spec.cwd,
        "--sandbox",
        spec.sandbox,
        "--output-last-message",
        spec.output,
        "-",
    ]


def deepseek_endpoint(env: dict[str, str]) -> str:
    return env.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1/chat/completions")


def require_deepseek_key(env: dict[str, str]) -> str:
    key = env.get("DEEPSEEK_API_KEY", "")
    if not key:
        raise RoutingError("DEEPSEEK_API_KEY is required for deepseek provider")
    return key


def shell_quote(args: list[str]) -> str:
    import shlex

    return " ".join(shlex.quote(arg) for arg in args)


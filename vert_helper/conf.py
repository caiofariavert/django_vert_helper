from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Mapping

from django.conf import settings as django_settings
from django.core.exceptions import ImproperlyConfigured

DEFAULTS: dict[str, Any] = {
    "ENABLED": True,
    "API_TIMEOUT": 5,
    "SERVICE_URL": None,
}

PREFIX = "VERT_HELPER_"


@dataclass(frozen=True)
class VertHelperSettings:
    enabled: bool
    api_timeout: int
    service_url: str | None


def _coerce_int(key: str, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ImproperlyConfigured(f"VERT_HELPER {key} deve ser inteiro.")
    return value


def _load_raw_settings() -> dict[str, Any]:
    raw_group = getattr(django_settings, "VERT_HELPER", {})
    if raw_group is None:
        raw_group = {}

    if not isinstance(raw_group, Mapping):
        raise ImproperlyConfigured(
            "VERT_HELPER deve ser um dict no settings.py."
        )

    merged = DEFAULTS.copy()
    merged.update(raw_group)

    for key in DEFAULTS:
        prefixed_key = f"{PREFIX}{key}"
        if hasattr(django_settings, prefixed_key):
            merged[key] = getattr(django_settings, prefixed_key)

    return merged


@lru_cache
def get_vert_helper_settings() -> VertHelperSettings:
    raw = _load_raw_settings()

    service_url = raw["SERVICE_URL"]
    if service_url is not None and not isinstance(service_url, str):
        raise ImproperlyConfigured(
            "VERT_HELPER SERVICE_URL deve ser string ou None."
        )

    return VertHelperSettings(
        enabled=bool(raw["ENABLED"]),
        api_timeout=_coerce_int("API_TIMEOUT", raw["API_TIMEOUT"]),
        service_url=service_url,
    )


def reload_vert_helper_settings() -> None:
    get_vert_helper_settings.cache_clear()

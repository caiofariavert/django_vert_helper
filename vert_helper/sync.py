from __future__ import annotations

from importlib import import_module

from django.apps import apps
from django.conf import settings
from django.db import transaction

from .models import Action, Service
from .registry import get_registered_actions


def autodiscover_actions() -> None:
    for app_config in apps.get_app_configs():
        module_name = f"{app_config.name}.actions"
        try:
            import_module(module_name)
        except ModuleNotFoundError:
            continue


def _get_service_names_from_settings() -> set[str]:
    config = getattr(settings, "VERT_HELPER", {}) or {}
    services_cfg = config.get("SERVICES", {})
    if not isinstance(services_cfg, dict):
        return set()
    return {
        str(name).strip()
        for name in services_cfg.keys()
        if str(name).strip()
    }


@transaction.atomic
def sync_services_from_settings() -> dict[str, int]:
    configured_names = _get_service_names_from_settings()

    created = 0
    reactivated = 0
    deactivated = 0

    existing_services = {s.name: s for s in Service.all_objects.all()}

    for service_name in configured_names:
        service = existing_services.get(service_name)
        if not service:
            Service.all_objects.create(name=service_name, is_active=True)
            created += 1
            continue

        if not service.is_active:
            service.is_active = True
            service.save(update_fields=["is_active", "updated_at"])
            reactivated += 1

    for service in Service.all_objects.filter(is_active=True):
        if service.name not in configured_names:
            service.is_active = False
            service.save(update_fields=["is_active", "updated_at"])
            deactivated += 1

    return {
        "created": created,
        "reactivated": reactivated,
        "deactivated": deactivated,
    }


@transaction.atomic
def sync_actions_from_registry() -> dict[str, int]:
    autodiscover_actions()
    registered = get_registered_actions()

    created = 0
    updated = 0
    deleted = 0

    active_services = {s.name: s for s in Service.objects.all()}

    seen_slugs: set[str] = set()
    for slug, action_def in registered.items():
        action, was_created = Action.objects.update_or_create(
            slug=slug,
            defaults={
                "name": action_def.name,
                "description": action_def.description,
                "function_path": action_def.function_path,
                "status": Action.Status.ACTIVE,
            },
        )

        seen_slugs.add(slug)

        service_objects = [
            active_services[name]
            for name in action_def.services
            if name in active_services
        ]
        action.services.set(service_objects)

        if was_created:
            created += 1
        else:
            updated += 1

    if seen_slugs:
        deleted, _ = Action.objects.exclude(slug__in=seen_slugs).delete()

    return {
        "created": created,
        "updated": updated,
        "deleted": deleted,
    }

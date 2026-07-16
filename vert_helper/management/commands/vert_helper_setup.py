from django.core.management.base import BaseCommand

from vert_helper.sync import (
    ensure_scheduler_registration,
    sync_actions_from_registry,
    sync_services_from_settings,
)


class Command(BaseCommand):
    help = "Setup completo do vert_helper (services + actions + scheduler)."

    def handle(self, *args, **options):
        services_result = sync_services_from_settings()
        actions_result = sync_actions_from_registry()
        scheduler_message = ensure_scheduler_registration()

        self.stdout.write(
            self.style.SUCCESS("Setup do vert_helper concluido.")
        )
        self.stdout.write(
            "Services -> "
            f"Criados: {services_result['created']}, "
            f"Reativados: {services_result['reactivated']}, "
            f"Desativados: {services_result['deactivated']}"
        )
        self.stdout.write(
            "Actions -> "
            f"Criadas: {actions_result['created']}, "
            f"Atualizadas: {actions_result['updated']}, "
            f"Deletadas: {actions_result['deleted']}"
        )
        self.stdout.write(f"Scheduler -> {scheduler_message}")

from django.core.management.base import BaseCommand

from apps.network.services import seed_network


class Command(BaseCommand):
    help = "Add the Nyabugogo roads and intersections (safe to run more than once)."

    def handle(self, *args, **options):
        result = seed_network()
        self.stdout.write(self.style.SUCCESS(
            f"Seeded {result['intersections']} intersections and {result['roads']} roads."))

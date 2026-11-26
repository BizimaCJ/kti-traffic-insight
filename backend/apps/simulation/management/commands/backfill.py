from django.core.management.base import BaseCommand, CommandError

from apps.simulation.generator import SimulatedDataGenerator, SimulationError


class Command(BaseCommand):
    help = "Create simulated traffic history for the past few days (for the History page and 'leave later' estimates)."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=7)
        parser.add_argument("--step", type=int, default=10, help="minutes between readings")

    def handle(self, *args, **options):
        if not 1 <= options["days"] <= 90:
            raise CommandError("--days must be between 1 and 90.")
        if options["step"] < 1:
            raise CommandError("--step must be at least 1 minute.")
        try:
            count = SimulatedDataGenerator("normal").backfill_history(options["days"], options["step"])
        except SimulationError as exc:
            raise CommandError(str(exc))
        self.stdout.write(self.style.SUCCESS(f"Saved {count} simulated readings covering the last {options['days']} days."))

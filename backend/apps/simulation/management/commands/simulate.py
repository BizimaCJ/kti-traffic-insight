import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.simulation.generator import SimulatedDataGenerator, SimulationError
from apps.simulation.scenarios import Scenario


class Command(BaseCommand):
    help = "Generate simulated traffic data (FR 21). Use --loop to keep it running."

    def add_arguments(self, parser):
        parser.add_argument("--scenario", default=None, choices=["auto"] + [s.value.lower() for s in Scenario])
        parser.add_argument("--loop", action="store_true", help="keep running until stopped (Ctrl+C)")
        parser.add_argument("--interval", type=int, default=None, help="seconds between cycles when looping")
        parser.add_argument("--cycles", type=int, default=0, help="stop after N cycles when looping (0 = forever)")

    def handle(self, *args, **options):
        generator = SimulatedDataGenerator(
            options["scenario"] or settings.SIMULATION_SCENARIO,
            refresh_interval_seconds=options["interval"],
        )
        cycles = 0
        try:
            while True:
                try:
                    r = generator.run_cycle()
                except SimulationError as exc:
                    raise CommandError(str(exc))
                cycles += 1
                local = timezone.localtime(r.recorded_at)
                self.stdout.write(
                    f"[{local:%H:%M:%S}] {r.scenario.value}: {r.conditions_created} conditions, "
                    f"incidents +{r.incidents_created}/-{r.incidents_resolved}, alerts +{r.alerts_created}/-{r.alerts_cleared}")
                if not options["loop"] or (options["cycles"] and cycles >= options["cycles"]):
                    return
                time.sleep(generator.refresh_interval_seconds)
        except KeyboardInterrupt:
            self.stdout.write("\nStopped.")

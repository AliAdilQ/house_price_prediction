from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from predictor.ml.dataset import generate_dataset


class Command(BaseCommand):
    help = "Generate the reproducible synthetic demo CSV (explicit --overwrite required)."

    def add_arguments(self, parser):
        parser.add_argument("--rows", type=int, default=1600)
        parser.add_argument("--overwrite", action="store_true")

    def handle(self, *args, **options):
        if settings.DATASET_PATH.exists() and not options["overwrite"]:
            raise CommandError("Dataset exists. Use --overwrite to replace it.")
        try:
            frame = generate_dataset(settings.DATASET_PATH, rows=options["rows"])
        except ValueError as error:
            raise CommandError(str(error)) from error
        self.stdout.write(self.style.SUCCESS(f"Generated {len(frame):,} synthetic rows."))

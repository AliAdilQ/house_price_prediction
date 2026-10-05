from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from predictor.ml.model_training import train


class Command(BaseCommand):
    help = "Compare three regression pipelines and save the CV-selected model."

    def handle(self, *args, **options):
        try:
            metadata = train(
                settings.DATASET_PATH, settings.MODEL_PATH, settings.MODEL_METADATA_PATH
            )
        except (OSError, ValueError) as error:
            raise CommandError(str(error)) from error
        self.stdout.write("Model comparison: 3-fold validation (training split only)")
        for score in metadata["comparison"]:
            self.stdout.write(
                f"{score['name']:<20} R² {score['r2']:.4f}  "
                f"MAE ${score['mae']:,.2f}  RMSE ${score['rmse']:,.2f}"
            )
        self.stdout.write(self.style.SUCCESS(f"Selected Model: {metadata['selected_model']}"))
        score = metadata["test_metrics"]
        self.stdout.write(
            f"Untouched test set: R² {score['r2']:.4f}, MAE ${score['mae']:,.2f}, "
            f"RMSE ${score['rmse']:,.2f} ({metadata['test_rows']} rows)"
        )

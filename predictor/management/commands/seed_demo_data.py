from datetime import timedelta

import pandas as pd
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from predictor.ml.features import FEATURES
from predictor.ml.service import PredictionUnavailable, estimate_price
from predictor.models import Prediction


class Command(BaseCommand):
    help = "Create a LOCAL demo superuser and 20 idempotent sample estimates."

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Demo seeding is disabled when DEBUG=False.")
        try:
            sample = pd.read_csv(settings.DATASET_PATH).sample(n=20, random_state=19)
            # Check the artifact before creating any account or record.
            estimates = [(row, estimate_price(row)) for row in sample[FEATURES].to_dict("records")]
        except (OSError, ValueError, PredictionUnavailable) as error:
            raise CommandError(f"Train the model before seeding: {error}") from error
        user, created = get_user_model().objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@example.com",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            user.set_password("Admin@12345")
            user.save()
        elif not user.is_superuser:
            raise CommandError("An existing non-superuser named admin will not be changed.")
        added = 0
        for index, (features, (price, model)) in enumerate(estimates):
            prediction, new = Prediction.objects.get_or_create(
                demo_key=f"demo-v1-{index:02d}",
                defaults={**features, "predicted_price": price, "model_name": model},
            )
            if new:
                Prediction.objects.filter(pk=prediction.pk).update(
                    created_at=timezone.now() - timedelta(hours=index * 7)
                )
                added += 1
        self.stdout.write(
            self.style.SUCCESS(
                f"Demo admin {'created' if created else 'already exists (password unchanged)'}. "
                f"Added {added} predictions. Local demonstration only."
            )
        )

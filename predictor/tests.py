"""Behavioral tests covering HTTP, persistence, demo safety, and actual ML inference."""

import hashlib
import io
import json
import tempfile
import uuid
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import OperationalError
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from .forms import PredictionForm
from .ml.dataset import generate_dataset
from .ml.features import FEATURES, LOCATIONS
from .ml.preprocessing import load_dataset
from .ml.service import PredictionUnavailable, estimate_price, model_metadata
from .models import Prediction

VALID_PROPERTY = {
    "location": "Riverside",
    "area_sqft": 1800,
    "bedrooms": 3,
    "bathrooms": 2,
    "floors": 2,
    "property_age": 8,
    "parking_spaces": 1,
    "property_type": "Detached",
    "furnishing_status": "Semi-furnished",
    "distance_city_center": 5.5,
    "nearby_school": True,
    "nearby_hospital": False,
}


class PageTests(TestCase):
    def test_main_pages_load(self):
        for name in ["home", "predict", "history", "about"]:
            with self.subTest(page=name):
                response = self.client.get(reverse(f"predictor:{name}"))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "habitat")

    def test_empty_history_has_helpful_state(self):
        self.assertContains(self.client.get(reverse("predictor:history")), "Your first estimate")

    @override_settings(DEBUG=False)
    def test_unknown_url_uses_custom_404(self):
        response = self.client.get("/this-address-does-not-exist/")
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")

    def test_unknown_result_is_404(self):
        response = self.client.get(reverse("predictor:result", args=[uuid.uuid4()]))
        self.assertEqual(response.status_code, 404)

    def test_database_failure_is_graceful(self):
        with patch(
            "predictor.views.Prediction.objects.count", side_effect=OperationalError("unavailable")
        ):
            with self.assertLogs("predictor", level="ERROR"):
                response = self.client.get(reverse("predictor:home"))
        self.assertEqual(response.status_code, 503)
        self.assertNotContains(response, "Traceback", status_code=503)


class PredictionTests(TestCase):
    def test_real_prediction_is_saved_and_redirected(self):
        response = self.client.post(reverse("predictor:predict"), VALID_PROPERTY)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Prediction.objects.count(), 1)
        prediction = Prediction.objects.get()
        self.assertGreater(prediction.predicted_price, 0)
        self.assertEqual(prediction.location, "Riverside")
        self.assertEqual(prediction.model_name, model_metadata()["selected_model"])
        result = self.client.get(response.url)
        self.assertContains(result, "Your estimate")
        self.assertContains(result, "professional real-estate valuation advice")
        self.assertContains(result, "1,800 sq ft")
        self.client.get(response.url)
        self.assertEqual(Prediction.objects.count(), 1)

    def test_invalid_numeric_inputs_do_not_create_records(self):
        for field, bad in [
            ("area_sqft", -1),
            ("bedrooms", 20),
            ("property_age", -3),
            ("distance_city_center", "NaN"),
            ("distance_city_center", "inf"),
            ("bedrooms", "2.5"),
        ]:
            with self.subTest(field=field, value=bad):
                response = self.client.post(
                    reverse("predictor:predict"), {**VALID_PROPERTY, field: bad}
                )
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context["form"].errors)
                self.assertEqual(Prediction.objects.count(), 0)

    def test_empty_submission_displays_validation(self):
        response = self.client.post(reverse("predictor:predict"), {})
        self.assertTrue(response.context["form"].errors)
        self.assertEqual(Prediction.objects.count(), 0)

    def test_invalid_category_is_rejected(self):
        response = self.client.post(
            reverse("predictor:predict"), {**VALID_PROPERTY, "location": "Unknown"}
        )
        self.assertIn("location", response.context["form"].errors)
        self.assertEqual(Prediction.objects.count(), 0)

    def test_impossible_layout_is_rejected(self):
        form = PredictionForm({**VALID_PROPERTY, "area_sqft": 400, "bedrooms": 6})
        self.assertFalse(form.is_valid())
        self.assertIn("area_sqft", form.errors)
        apartment = PredictionForm({**VALID_PROPERTY, "property_type": "Apartment"})
        self.assertFalse(apartment.is_valid())
        self.assertIn("floors", apartment.errors)

    def test_missing_model_shows_safe_error_and_saves_nothing(self):
        with override_settings(MODEL_PATH=Path("missing-model.joblib")):
            with self.assertLogs("predictor", level="WARNING"):
                response = self.client.post(reverse("predictor:predict"), VALID_PROPERTY)
        self.assertEqual(response.status_code, 503)
        self.assertContains(response, "model is unavailable", status_code=503)
        self.assertEqual(Prediction.objects.count(), 0)

    def test_database_save_failure_shows_safe_error(self):
        with patch(
            "predictor.views.Prediction.save", side_effect=OperationalError("database locked")
        ):
            with self.assertLogs("predictor", level="ERROR"):
                response = self.client.post(reverse("predictor:predict"), VALID_PROPERTY)
        self.assertEqual(response.status_code, 503)
        self.assertContains(response, "couldn&#x27;t save", status_code=503)
        self.assertEqual(Prediction.objects.count(), 0)

    def test_csrf_is_required(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(reverse("predictor:predict"), VALID_PROPERTY)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Prediction.objects.count(), 0)

    def test_prediction_rejects_other_http_methods(self):
        self.assertEqual(self.client.put(reverse("predictor:predict")).status_code, 405)


@override_settings(DEBUG=True)
class DemoAndAdminTests(TestCase):
    def setUp(self):
        call_command("seed_demo_data", stdout=io.StringIO())

    def test_seed_is_idempotent_and_preserves_existing_password(self):
        user = get_user_model().objects.get(username="admin")
        self.assertTrue(user.is_superuser and user.is_staff)
        self.assertTrue(user.check_password("Admin@12345"))
        self.assertEqual(Prediction.objects.count(), 20)
        user.set_password("A-new-local-password-42")
        user.save()
        call_command("seed_demo_data", stdout=io.StringIO())
        user.refresh_from_db()
        self.assertTrue(user.check_password("A-new-local-password-42"))
        self.assertEqual(Prediction.objects.count(), 20)

    @override_settings(DEBUG=False)
    def test_seed_is_blocked_in_production(self):
        with self.assertRaises(CommandError):
            call_command("seed_demo_data", stdout=io.StringIO())

    def test_admin_login_list_filters_and_detail(self):
        self.assertTrue(self.client.login(username="admin", password="Admin@12345"))
        self.assertContains(
            self.client.get(reverse("admin:index")), "House Price Prediction Administration"
        )
        url = reverse("admin:predictor_prediction_changelist")
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.get(url, {"q": "Riverside"}).status_code, 200)
        self.assertEqual(self.client.get(url, {"location__exact": "Oakwood"}).status_code, 200)
        prediction = Prediction.objects.first()
        self.assertEqual(
            self.client.get(
                reverse("admin:predictor_prediction_change", args=[prediction.pk])
            ).status_code,
            200,
        )

    def test_history_pagination_search_and_filter(self):
        url = reverse("predictor:history")
        first = self.client.get(url)
        self.assertEqual(len(first.context["page_obj"]), 10)
        self.assertEqual(first.context["page_obj"].paginator.num_pages, 2)
        self.assertEqual(self.client.get(url, {"page": "invalid"}).status_code, 200)
        self.assertEqual(self.client.get(url, {"page": 999}).context["page_obj"].number, 2)
        filtered = self.client.get(url, {"location": "Riverside", "q": "Riverside"})
        self.assertTrue(all(item.location == "Riverside" for item in filtered.context["page_obj"]))
        self.assertContains(self.client.get(url, {"q": "no match exists"}), "No estimates match")

    def test_home_chart_uses_real_database_records(self):
        response = self.client.get(reverse("predictor:home"))
        self.assertEqual(response.context["total_predictions"], 20)
        self.assertTrue(response.context["chart_data"]["values"])
        self.assertEqual(response.context["metrics"], model_metadata()["test_metrics"])


class MachineLearningTests(SimpleTestCase):
    def test_bundled_pipeline_predicts_all_locations(self):
        for location in LOCATIONS:
            with self.subTest(location=location):
                price, name = estimate_price({**VALID_PROPERTY, "location": location})
                self.assertGreater(price, 0)
                self.assertTrue(name)

    def test_larger_otherwise_identical_property_has_higher_estimate(self):
        smaller, _ = estimate_price({**VALID_PROPERTY, "area_sqft": 1000})
        larger, _ = estimate_price({**VALID_PROPERTY, "area_sqft": 3000})
        self.assertGreater(larger, smaller)

    def test_metadata_matches_actual_dataset(self):
        frame, _ = load_dataset(settings.DATASET_PATH)
        metadata = model_metadata()
        self.assertEqual(len(frame), metadata["dataset_rows"])
        self.assertEqual(metadata["training_rows"] + metadata["test_rows"], len(frame))
        self.assertEqual(metadata["features"], FEATURES)
        self.assertEqual(
            hashlib.sha256(settings.DATASET_PATH.read_bytes()).hexdigest(),
            metadata["dataset_sha256"],
        )
        self.assertEqual(len(metadata["comparison"]), 3)
        self.assertTrue(0 < metadata["test_metrics"]["r2"] <= 1)

    def test_generator_is_deterministic_and_enforces_domains(self):
        with tempfile.TemporaryDirectory(dir=settings.BASE_DIR) as directory:
            path = Path(directory) / "sample.csv"
            first = generate_dataset(path, rows=500)
            second = generate_dataset(path, rows=500)
            pd.testing.assert_frame_equal(first, second)
            clean, removed = load_dataset(path)
            self.assertEqual(len(clean), 500)
            self.assertEqual(removed, 0)
            self.assertTrue((clean.price > 0).all())

    def test_invalid_csv_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=settings.BASE_DIR) as directory:
            path = Path(directory) / "invalid.csv"
            path.write_text("location,price\nOakwood,1234\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing columns"):
                load_dataset(path)

    def test_corrupted_model_is_rejected_before_deserialization(self):
        with tempfile.TemporaryDirectory(dir=settings.BASE_DIR) as directory:
            path = Path(directory) / "corrupt.joblib"
            path.write_bytes(b"invalid artifact")
            with override_settings(MODEL_PATH=path):
                with self.assertRaisesRegex(PredictionUnavailable, "verified"):
                    estimate_price(VALID_PROPERTY)

    def test_incompatible_library_version_is_rejected(self):
        metadata = model_metadata()
        metadata["versions"]["scikit_learn"] = "0.0"
        with tempfile.TemporaryDirectory(dir=settings.BASE_DIR) as directory:
            path = Path(directory) / "metadata.json"
            path.write_text(json.dumps(metadata), encoding="utf-8")
            with override_settings(MODEL_METADATA_PATH=path):
                with self.assertRaisesRegex(PredictionUnavailable, "retraining"):
                    estimate_price(VALID_PROPERTY)

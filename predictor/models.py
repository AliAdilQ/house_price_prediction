import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .ml.features import FURNISHING_STATUSES, LOCATIONS, NUMERIC_LIMITS, PROPERTY_TYPES


def limits(name):
    low, high = NUMERIC_LIMITS[name]
    return [MinValueValidator(low), MaxValueValidator(high)]


class Prediction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    location = models.CharField(max_length=32, choices=[(v, v) for v in LOCATIONS])
    area_sqft = models.PositiveIntegerField(validators=limits("area_sqft"))
    bedrooms = models.PositiveSmallIntegerField(validators=limits("bedrooms"))
    bathrooms = models.PositiveSmallIntegerField(validators=limits("bathrooms"))
    floors = models.PositiveSmallIntegerField(validators=limits("floors"))
    property_age = models.PositiveSmallIntegerField(validators=limits("property_age"))
    parking_spaces = models.PositiveSmallIntegerField(validators=limits("parking_spaces"))
    property_type = models.CharField(max_length=24, choices=[(v, v) for v in PROPERTY_TYPES])
    furnishing_status = models.CharField(
        max_length=24, choices=[(v, v) for v in FURNISHING_STATUSES]
    )
    distance_city_center = models.FloatField(validators=limits("distance_city_center"))
    nearby_school = models.BooleanField(default=False)
    nearby_hospital = models.BooleanField(default=False)
    predicted_price = models.DecimalField(
        max_digits=14, decimal_places=2, validators=[MinValueValidator(0)]
    )
    model_name = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    demo_key = models.CharField(max_length=32, unique=True, null=True, blank=True, editable=False)

    class Meta:
        ordering = ["-created_at", "id"]
        indexes = [models.Index(fields=["location", "property_type"])]

    def __str__(self):
        return f"{self.property_type} in {self.location} — ${self.predicted_price:,.0f}"

    @property
    def price_per_sqft(self):
        return self.predicted_price / self.area_sqft

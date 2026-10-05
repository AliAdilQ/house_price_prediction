"""Reproducible synthetic data, not observations of a real housing market."""

import numpy as np
import pandas as pd

from .features import FEATURES, FURNISHING_STATUSES, LOCATIONS, PROPERTY_TYPES


def generate_dataset(path, rows=1600, seed=42):
    if rows < 500:
        raise ValueError("Generate at least 500 records.")
    rng = np.random.default_rng(seed)
    location_rates = dict(zip(LOCATIONS, [300, 265, 230, 210, 165, 245]))
    type_premiums = dict(zip(PROPERTY_TYPES, [-18000, 15000, 40000, 105000]))
    furnishing_premiums = dict(zip(FURNISHING_STATUSES, [0, 14000, 30000]))
    records = []
    for _ in range(rows):
        location = rng.choice(LOCATIONS)
        kind = rng.choice(PROPERTY_TYPES, p=[0.3, 0.23, 0.35, 0.12])
        bedrooms = int(rng.integers(1, 7 if kind == "Villa" else 6))
        bathrooms = int(rng.integers(1, min(bedrooms + 1, 5) + 1))
        area = int(np.clip(rng.normal(450 + bedrooms * 420, 280), 400, 6000))
        area = max(area, 120 * (bedrooms + bathrooms))
        floors = 1 if kind == "Apartment" else int(rng.integers(1, 4))
        age = int(rng.integers(0, 61))
        parking = int(rng.integers(0, 5))
        furnishing = rng.choice(FURNISHING_STATUSES)
        distance = round(float(rng.uniform(0.5, 35)), 1)
        school, hospital = int(rng.random() < 0.7), int(rng.random() < 0.55)
        # Area/location interaction, depreciation, amenities, and market noise.
        structural_value = area * location_rates[location] * (1 - 0.003 * age)
        price = (
            structural_value
            + type_premiums[kind]
            + furnishing_premiums[furnishing]
            + bedrooms * 6500
            + bathrooms * 11000
            + parking * 9000
            + floors * 5000
            + 65000 * np.exp(-distance / 10)
            + school * 12000
            + hospital * 9000
        )
        price *= rng.normal(1, 0.045)
        records.append(
            {
                "location": location,
                "area_sqft": area,
                "bedrooms": bedrooms,
                "bathrooms": bathrooms,
                "floors": floors,
                "property_age": age,
                "parking_spaces": parking,
                "property_type": kind,
                "furnishing_status": furnishing,
                "distance_city_center": distance,
                "nearby_school": school,
                "nearby_hospital": hospital,
                "price": round(max(float(price), 50000), 2),
            }
        )
    frame = pd.DataFrame(records)[FEATURES + ["price"]]
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, lineterminator="\n")
    return frame

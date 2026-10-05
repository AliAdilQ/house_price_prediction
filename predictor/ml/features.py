"""One feature schema shared by dataset generation, forms, and training."""

LOCATIONS = ["Downtown", "Riverside", "Oakwood", "West End", "Greenfield", "Hillcrest"]
PROPERTY_TYPES = ["Apartment", "Townhouse", "Detached", "Villa"]
FURNISHING_STATUSES = ["Unfurnished", "Semi-furnished", "Fully furnished"]
CATEGORICAL_FEATURES = ["location", "property_type", "furnishing_status"]
NUMERIC_LIMITS = {
    "area_sqft": (400, 6000),
    "bedrooms": (1, 6),
    "bathrooms": (1, 5),
    "floors": (1, 3),
    "property_age": (0, 60),
    "parking_spaces": (0, 4),
    "distance_city_center": (0.5, 35),
    "nearby_school": (0, 1),
    "nearby_hospital": (0, 1),
}
NUMERIC_FEATURES = list(NUMERIC_LIMITS)
FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES
CATEGORY_VALUES = {
    "location": LOCATIONS,
    "property_type": PROPERTY_TYPES,
    "furnishing_status": FURNISHING_STATUSES,
}

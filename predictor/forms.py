from django import forms

from .models import Prediction


class PredictionForm(forms.ModelForm):
    class Meta:
        model = Prediction
        fields = [
            "location",
            "property_type",
            "area_sqft",
            "bedrooms",
            "bathrooms",
            "floors",
            "property_age",
            "parking_spaces",
            "furnishing_status",
            "distance_city_center",
            "nearby_school",
            "nearby_hospital",
        ]
        labels = {
            "area_sqft": "Living area (sq ft)",
            "property_age": "Property age (years)",
            "distance_city_center": "Distance to city center (km)",
            "parking_spaces": "Parking spaces",
            "furnishing_status": "Furnishing",
            "nearby_school": "School nearby",
            "nearby_hospital": "Hospital nearby",
        }
        help_texts = {
            "location": "Choose one of the six demo neighborhoods.",
            "area_sqft": "Total interior floor area, between 400 and 6,000 sq ft.",
            "distance_city_center": "Between 0.5 and 35 kilometers.",
            "nearby_school": "Within approximately 2 km.",
            "nearby_hospital": "Within approximately 5 km.",
        }
        widgets = {"distance_city_center": forms.NumberInput(attrs={"step": "0.1"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .ml.features import NUMERIC_LIMITS

        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                css_class = "form-check-input"
            elif isinstance(field.widget, forms.Select):
                css_class = "form-select"
                field.empty_label = "Select an option"
                field.choices = [("", "Select an option")] + [
                    (value, label) for value, label in field.choices if value
                ]
            else:
                css_class = "form-control"
            field.widget.attrs["class"] = css_class
            field.widget.attrs["aria-describedby"] = f"hint_{name} error_{name}"
            if name in NUMERIC_LIMITS and not isinstance(field.widget, forms.CheckboxInput):
                low, high = NUMERIC_LIMITS[name]
                field.widget.attrs.update({"min": low, "max": high})
                field.widget.attrs.setdefault("step", "1")
        for name, placeholder in {"area_sqft": "e.g. 1,800", "property_age": "e.g. 8"}.items():
            self.fields[name].widget.attrs["placeholder"] = placeholder
        if self.is_bound:
            for name in self.errors:
                if name in self.fields:
                    self.fields[name].widget.attrs["class"] += " is-invalid"
                    self.fields[name].widget.attrs["aria-invalid"] = "true"

    def clean(self):
        data = super().clean()
        area, beds, baths = (data.get(key) for key in ("area_sqft", "bedrooms", "bathrooms"))
        if all(value is not None for value in (area, beds, baths)):
            if area < 120 * (beds + baths):
                self.add_error("area_sqft", "Allow at least 120 sq ft per bedroom and bathroom.")
        if data.get("property_type") == "Apartment" and data.get("floors", 1) != 1:
            self.add_error("floors", "An apartment's interior occupies one floor in this demo.")
        return data

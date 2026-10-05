from django.contrib import admin

from .models import Prediction

admin.site.site_header = "House Price Prediction Administration"
admin.site.site_title = "House Price Prediction Admin"
admin.site.index_title = "Dashboard"


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = [
        "location",
        "property_type",
        "area_sqft",
        "bedrooms",
        "predicted_price",
        "created_at",
    ]
    search_fields = ["location", "property_type", "model_name", "id"]
    list_filter = ["location", "property_type", "furnishing_status", "created_at"]
    ordering = ["-created_at"]
    date_hierarchy = "created_at"
    readonly_fields = ["id", "predicted_price", "model_name", "created_at", "demo_key"]
    list_per_page = 25

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        # Prediction records are an immutable audit of the original estimate.
        return False

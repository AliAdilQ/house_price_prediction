import logging

from django.core.paginator import Paginator
from django.db import DatabaseError
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import PredictionForm
from .ml.features import LOCATIONS, PROPERTY_TYPES
from .ml.service import PredictionUnavailable, estimate_price, model_metadata
from .models import Prediction

logger = logging.getLogger(__name__)


def unavailable(request):
    return render(request, "503.html", status=503)


def home(request):
    metadata = model_metadata()
    try:
        total = Prediction.objects.count()
        averages = list(
            Prediction.objects.values("location")
            .annotate(average=Avg("predicted_price"), count=Count("id"))
            .order_by("location")
        )
        recent = list(Prediction.objects.all()[:4])
    except DatabaseError:
        logger.exception("Unable to read home statistics")
        return unavailable(request)
    chart = {
        "labels": [item["location"] for item in averages],
        "values": [round(float(item["average"]), 2) for item in averages],
    }
    return render(
        request,
        "home.html",
        {
            "total_predictions": total,
            "metadata": metadata,
            "metrics": metadata.get("test_metrics", {}),
            "chart_data": chart,
            "recent": recent,
        },
    )


@require_http_methods(["GET", "POST"])
def predict(request):
    form = PredictionForm(request.POST if request.method == "POST" else None)
    status = 200
    if request.method == "POST" and form.is_valid():
        try:
            price, model_name = estimate_price(form.cleaned_data)
            prediction = form.save(commit=False)
            prediction.predicted_price = price
            prediction.model_name = model_name
            prediction.save()
            return redirect("predictor:result", pk=prediction.pk)
        except PredictionUnavailable as error:
            logger.warning("Prediction unavailable: %s", error, exc_info=True)
            form.add_error(None, str(error))
            status = 503
        except DatabaseError:
            logger.exception("Unable to save prediction")
            form.add_error(None, "We couldn't save this estimate. Please try again later.")
            status = 503
    return render(
        request,
        "predict.html",
        {
            "form": form,
            "metadata": model_metadata(),
        },
        status=status,
    )


def result(request, pk):
    try:
        prediction = get_object_or_404(Prediction, pk=pk)
    except DatabaseError:
        logger.exception("Unable to read prediction result")
        return unavailable(request)
    return render(request, "result.html", {"prediction": prediction})


def history(request):
    query = request.GET.get("q", "").strip()[:100]
    location = request.GET.get("location", "")
    kind = request.GET.get("type", "")
    predictions = Prediction.objects.all()
    if query:
        from django.db.models import Q

        predictions = predictions.filter(
            Q(location__icontains=query) | Q(property_type__icontains=query)
        )
    if location in LOCATIONS:
        predictions = predictions.filter(location=location)
    if kind in PROPERTY_TYPES:
        predictions = predictions.filter(property_type=kind)
    try:
        summary = predictions.aggregate(count=Count("id"), average=Avg("predicted_price"))
        page = Paginator(predictions, 10).get_page(request.GET.get("page"))
        list(page.object_list)
    except DatabaseError:
        logger.exception("Unable to read prediction history")
        return unavailable(request)
    params = request.GET.copy()
    params.pop("page", None)
    return render(
        request,
        "history.html",
        {
            "page_obj": page,
            "summary": summary,
            "q": query,
            "locations": LOCATIONS,
            "property_types": PROPERTY_TYPES,
            "selected_location": location,
            "selected_type": kind,
            "filter_query": params.urlencode(),
        },
    )


def about(request):
    metadata = model_metadata()
    return render(
        request,
        "about.html",
        {
            "metadata": metadata,
            "metrics": metadata.get("test_metrics", {}),
        },
    )


def page_not_found(request, exception):
    return render(request, "404.html", status=404)


def server_error(request):
    return render(request, "500.html", status=500)

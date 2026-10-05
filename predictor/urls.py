from django.urls import path

from . import views

app_name = "predictor"
urlpatterns = [
    path("", views.home, name="home"),
    path("predict/", views.predict, name="predict"),
    path("result/<uuid:pk>/", views.result, name="result"),
    path("history/", views.history, name="history"),
    path("about/", views.about, name="about"),
]

from django.urls import path
import views

urlpatterns = [
    path("", views.index, name="index"),
    path("api/benchmarks/", views.api_benchmarks, name="api_benchmarks"),
]
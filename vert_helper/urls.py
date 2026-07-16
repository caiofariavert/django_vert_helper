from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ActionViewSet, HealthcareView

router = DefaultRouter()
router.register(r"actions", ActionViewSet, basename="vert-helper-actions")

urlpatterns = [
    path(
        "api/helper/v1/healthcare/",
        HealthcareView.as_view(),
        name="vert-helper-healthcare",
    ),
    path("api/helper/v1/", include(router.urls)),
]

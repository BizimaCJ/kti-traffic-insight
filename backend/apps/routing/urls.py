from django.urls import path

from apps.routing.views import JourneyView

urlpatterns = [path("journeys", JourneyView.as_view())]

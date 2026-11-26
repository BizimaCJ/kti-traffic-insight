from django.urls import path

from apps.incidents.views import (AdminIncidentActionView, AdminIncidentListView,
                                  PublicIncidentListView, ReportIncidentView)

urlpatterns = [
    path("incidents", PublicIncidentListView.as_view()),
    path("incidents/report", ReportIncidentView.as_view()),
    path("admin/incidents", AdminIncidentListView.as_view()),
    path("admin/incidents/<int:pk>/<str:action>", AdminIncidentActionView.as_view()),
]

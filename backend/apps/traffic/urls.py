from django.urls import path

from apps.traffic.views import ConditionsView, HistoryView

urlpatterns = [
    path("traffic/conditions", ConditionsView.as_view()),
    path("traffic/history", HistoryView.as_view()),
]

from django.urls import path

from apps.overview.views import OverviewView

urlpatterns = [path("overview", OverviewView.as_view())]

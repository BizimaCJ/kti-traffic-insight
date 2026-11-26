from django.urls import path

from apps.network.views import NetworkView

urlpatterns = [path("network", NetworkView.as_view())]

from django.contrib import admin
from django.urls import include, path, re_path

from apps.core.views import SpaView

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("api/", include("apps.core.urls")),
    path("api/", include("apps.accounts.urls")),
    path("api/", include("apps.network.urls")),
    path("api/", include("apps.traffic.urls")),
    path("api/", include("apps.incidents.urls")),
    path("api/", include("apps.alerts.urls")),
    path("api/", include("apps.audit.urls")),
    path("api/", include("apps.routing.urls")),
    path("api/", include("apps.overview.urls")),
    # Everything else belongs to the React app (client-side routing)
    re_path(r"^(?!api/|django-admin/|static/).*$", SpaView.as_view(), name="spa"),
]

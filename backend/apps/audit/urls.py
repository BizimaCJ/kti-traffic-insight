from django.urls import path

from apps.audit.views import AuditLogView

urlpatterns = [path("admin/audit-log", AuditLogView.as_view())]

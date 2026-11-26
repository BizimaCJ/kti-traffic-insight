from django.urls import path

from apps.alerts.views import AdminAlertView, AdminAlertWithdrawView, PublicAlertListView

urlpatterns = [
    path("alerts", PublicAlertListView.as_view()),
    path("admin/alerts", AdminAlertView.as_view()),
    path("admin/alerts/<int:pk>/withdraw", AdminAlertWithdrawView.as_view()),
]

from django.urls import path

from apps.accounts.views import LoginView, LogoutView, SessionView

urlpatterns = [
    path("auth/session", SessionView.as_view()),
    path("auth/login", LoginView.as_view()),
    path("auth/logout", LogoutView.as_view()),
]

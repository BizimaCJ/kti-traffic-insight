from rest_framework.authentication import SessionAuthentication


class AdminSessionAuthentication(SessionAuthentication):
    """Session login with CSRF protection. Returns 401 (not 403) when the session is missing or expired."""

    def authenticate_header(self, request):
        return "Session"

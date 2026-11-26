from django.conf import settings
from django.db import connection
from django.http import HttpResponse
from django.views import View
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    def get(self, request):
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return Response({"status": "ok"})


class SpaView(View):
    """Serves the built React app for every non-API path."""

    def get(self, request, *args, **kwargs):
        index = settings.FRONTEND_DIST / "index.html"
        if index.exists():
            response = HttpResponse(index.read_text(encoding="utf-8"), content_type="text/html")
            response["Cache-Control"] = "no-cache"
            return response
        return HttpResponse(
            "<h1>Kigali Traffic Insight</h1><p>The front end has not been built yet. "
            "Run <code>npm install &amp;&amp; npm run build</code> in the frontend folder, "
            "or start it with <code>npm run dev</code>.</p>",
            status=200,
        )

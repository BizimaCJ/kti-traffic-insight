from django.core.paginator import EmptyPage, Paginator
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import AuditLog
from apps.audit.serializers import AuditLogSerializer
from apps.core.permissions import IsAdministrator


class AuditLogView(APIView):
    """Who did what and when (FR 19). Administrators only."""

    permission_classes = [IsAdministrator]

    def get(self, request):
        try:
            page_size = min(max(int(request.query_params.get("page_size", 25)), 1), 100)
            page_number = max(int(request.query_params.get("page", 1)), 1)
        except ValueError:
            page_size, page_number = 25, 1
        paginator = Paginator(AuditLog.objects.select_related("admin"), page_size)
        try:
            page = paginator.page(page_number)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)
        return Response({
            "count": paginator.count,
            "page": page.number,
            "pages": paginator.num_pages,
            "results": AuditLogSerializer(page.object_list, many=True).data,
        })

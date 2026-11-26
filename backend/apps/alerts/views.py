from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.alerts import services
from apps.alerts.models import Alert, AlertStatus
from apps.alerts.serializers import AdminAlertSerializer, PublicAlertSerializer, PublishAlertSerializer
from apps.core.permissions import IsAdministrator
from apps.network.models import Road


class PublicAlertListView(APIView):
    """Active alerts shown as banners (FR 6)."""

    def get(self, request):
        return Response(PublicAlertSerializer(services.list_active(), many=True).data)


class AdminAlertView(APIView):
    permission_classes = [IsAdministrator]

    def get(self, request):
        alerts = Alert.objects.select_related("road", "incident", "published_by", "withdrawn_by")
        wanted = request.query_params.get("status")
        if wanted in AlertStatus.values:
            alerts = alerts.filter(status=wanted)
        return Response({"results": AdminAlertSerializer(alerts[:100], many=True).data})

    def post(self, request):  # publish (FR 16)
        body = PublishAlertSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        road = None
        if body.validated_data.get("road"):
            road = Road.objects.filter(pk=body.validated_data["road"]).first()
            if not road:
                raise ValidationError({"road": "Unknown road."})
        alert = services.publish_manual(request.user, body.validated_data["message"], road)
        return Response(AdminAlertSerializer(alert).data, status=status.HTTP_201_CREATED)


class AdminAlertWithdrawView(APIView):
    permission_classes = [IsAdministrator]

    def post(self, request, pk):  # withdraw (FR 17)
        alert = services.withdraw(get_object_or_404(Alert, pk=pk), request.user)
        alert = Alert.objects.select_related("road", "incident", "published_by", "withdrawn_by").get(pk=alert.pk)
        return Response(AdminAlertSerializer(alert).data)

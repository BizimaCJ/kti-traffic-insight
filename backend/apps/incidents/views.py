from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsAdministrator
from apps.core.throttles import IncidentReportThrottle
from apps.incidents import services
from apps.incidents.models import Incident, IncidentStatus
from apps.incidents.serializers import (AdminIncidentSerializer, PublicIncidentSerializer,
                                        RejectSerializer, ReportSerializer)


class PublicIncidentListView(APIView):
    """Verified incidents that are not resolved (FR 2)."""

    def get(self, request):
        return Response(PublicIncidentSerializer(services.list_public(), many=True).data)


class ReportIncidentView(APIView):
    """Anonymous incident report - no login needed (FR 3)."""

    throttle_classes = [IncidentReportThrottle]

    def post(self, request):
        data = ReportSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        v = data.validated_data
        incident = services.submit_report(
            type=v["type"], description=v["description"], road=v["road"], intersection=v.get("intersection"),
            reporter_name=v["reporter_name"], reporter_contact=v["reporter_contact"],
        )
        return Response(
            {"reference": incident.reference, "status": incident.status,
             "message": "Report received. An administrator will review it before it is shown to other road users."},
            status=status.HTTP_201_CREATED,
        )


class AdminIncidentListView(APIView):
    permission_classes = [IsAdministrator]

    def get(self, request):
        incidents = Incident.objects.select_related("road", "intersection", "reviewed_by")
        wanted = request.query_params.get("status")
        if wanted and wanted in IncidentStatus.values:
            incidents = incidents.filter(status=wanted)
        counts = {s: Incident.objects.filter(status=s).count() for s in IncidentStatus.values}
        return Response({
            "counts": counts,
            "results": AdminIncidentSerializer(incidents[:200], many=True).data,
        })


class AdminIncidentActionView(APIView):
    """review / verify / reject / resolve one incident."""

    permission_classes = [IsAdministrator]

    def post(self, request, pk, action):
        incident = get_object_or_404(Incident, pk=pk)
        if action == "reject":
            body = RejectSerializer(data=request.data)
            body.is_valid(raise_exception=True)
            incident = services.reject(incident, request.user, body.validated_data["reason"])
        elif action in services.ACTIONS:
            incident = services.ACTIONS[action](incident, request.user)
        else:
            return Response({"detail": "Unknown action."}, status=status.HTTP_404_NOT_FOUND)
        incident = Incident.objects.select_related("road", "intersection", "reviewed_by").get(pk=incident.pk)
        return Response(AdminIncidentSerializer(incident).data)

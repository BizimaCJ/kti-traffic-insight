from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.alerts import services as alert_services
from apps.alerts.serializers import PublicAlertSerializer
from apps.incidents import services as incident_services
from apps.incidents.serializers import PublicIncidentSerializer
from apps.traffic import services as traffic_services
from apps.traffic.levels import worst_level
from apps.traffic.serializers import TrafficConditionSerializer


class OverviewView(APIView):
    """Everything the traffic overview page needs in one request (sequence diagram SD-1)."""

    def get(self, request):
        conditions = traffic_services.latest_conditions()
        incidents = list(incident_services.list_public())
        alerts = list(alert_services.list_active())
        return Response({
            "generated_at": timezone.now(),
            "has_data": bool(conditions),
            "simulated": any(c.is_simulated for c in conditions) or any(i.is_simulated for i in incidents),
            "worst_level": worst_level(c.level for c in conditions),
            "roads": TrafficConditionSerializer(conditions, many=True).data,
            "incidents": PublicIncidentSerializer(incidents, many=True).data,
            "alerts": PublicAlertSerializer(alerts, many=True).data,
        })

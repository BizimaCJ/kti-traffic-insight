from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.network.models import Road
from apps.traffic import services
from apps.traffic.serializers import TrafficConditionSerializer


class ConditionsView(APIView):
    """Latest traffic level for each road (FR 1)."""

    def get(self, request):
        return Response(TrafficConditionSerializer(services.latest_conditions(), many=True).data)


class HistoryView(APIView):
    """Stored traffic history for one road or all roads (FR 10). Read-only and public."""

    def get(self, request):
        range_key = request.query_params.get("range", "24h")
        if range_key not in services.RANGES:
            raise ValidationError({"range": "Choose 24h, 7d or 30d."})
        road_param = request.query_params.get("road", "all")
        road = None
        if road_param != "all":
            try:
                road = Road.objects.get(pk=int(road_param))
            except (ValueError, Road.DoesNotExist):
                raise ValidationError({"road": "Unknown road."})
        data = services.history(road.id if road else None, range_key)
        return Response({
            "road": {"id": road.id, "name": road.name} if road else None,
            "range": range_key,
            "count": data["count"],
            "simulated": any(c.is_simulated for c in data["recent"]) if data["recent"] else True,
            "points": data["points"],
            "recent": TrafficConditionSerializer(data["recent"], many=True).data,
        })

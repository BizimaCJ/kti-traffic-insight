from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.network.models import Intersection, Road
from apps.network.serializers import IntersectionSerializer, RoadSerializer


class NetworkView(APIView):
    """The intersections and roads (used by the map and by the journey and report forms)."""

    def get(self, request):
        roads = Road.objects.select_related("start_intersection", "end_intersection")
        return Response({
            "intersections": IntersectionSerializer(Intersection.objects.all(), many=True).data,
            "roads": RoadSerializer(roads, many=True).data,
            # The same numbers the system uses, so the screens never disagree with the rules
            "thresholds": {
                "free_flow_max": settings.FREE_FLOW_MAX_DELAY,
                "moderate_max": settings.MODERATE_MAX_DELAY,
                "heavy_max": settings.HEAVY_MAX_DELAY,
                "alert": settings.ALERT_DELAY_THRESHOLD,
            },
        })

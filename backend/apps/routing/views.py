from rest_framework.response import Response
from rest_framework.views import APIView

from apps.routing import services
from apps.routing.serializers import JourneySerializer


class JourneyView(APIView):
    """Enter an origin and destination, get the estimated delay and alternative routes."""

    def post(self, request):
        data = JourneySerializer(data=request.data)
        data.is_valid(raise_exception=True)
        v = data.validated_data
        return Response(services.plan_journey(v["origin"], v["destination"], v.get("departure_time")))

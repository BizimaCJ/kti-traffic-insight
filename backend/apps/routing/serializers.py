from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from apps.network.models import Intersection


class JourneySerializer(serializers.Serializer):
    origin = serializers.PrimaryKeyRelatedField(queryset=Intersection.objects.all())
    destination = serializers.PrimaryKeyRelatedField(queryset=Intersection.objects.all())
    departure_time = serializers.DateTimeField(required=False, allow_null=True)

    def validate(self, attrs):
        if attrs["origin"] == attrs["destination"]:
            raise serializers.ValidationError({"destination": "Choose a destination that is different from the origin."})
        when = attrs.get("departure_time")
        if when:
            now = timezone.now()
            if when < now - timedelta(minutes=15):
                raise serializers.ValidationError({"departure_time": "The departure time cannot be in the past."})
            if when > now + timedelta(hours=24):
                raise serializers.ValidationError({"departure_time": "Choose a departure time within the next 24 hours."})
        return attrs

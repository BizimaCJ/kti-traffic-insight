from rest_framework import serializers

from apps.traffic.models import TrafficCondition


class TrafficConditionSerializer(serializers.ModelSerializer):
    road_name = serializers.CharField(source="road.name")
    length_km = serializers.FloatField(source="road.length_km")

    class Meta:
        model = TrafficCondition
        fields = ["road_id", "road_name", "length_km", "level", "delay_minutes",
                  "average_speed_kmh", "recorded_at", "is_simulated"]

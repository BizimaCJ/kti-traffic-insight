from rest_framework import serializers

from apps.network.models import Intersection, Road


class IntersectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Intersection
        fields = ["id", "name", "node_type", "map_x", "map_y"]


class RoadSerializer(serializers.ModelSerializer):
    start_id = serializers.IntegerField(source="start_intersection_id")
    end_id = serializers.IntegerField(source="end_intersection_id")
    start_name = serializers.CharField(source="start_intersection.name")
    end_name = serializers.CharField(source="end_intersection.name")

    class Meta:
        model = Road
        fields = ["id", "name", "length_km", "start_id", "end_id", "start_name", "end_name"]

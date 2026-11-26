from rest_framework import serializers

from apps.incidents.models import Incident, IncidentType
from apps.network.models import Intersection, Road


class PublicIncidentSerializer(serializers.ModelSerializer):
    """What the public may see. Reporter details and rejection reasons are never included."""

    road_name = serializers.CharField(source="road.name")
    intersection_name = serializers.CharField(source="intersection.name", default=None)

    class Meta:
        model = Incident
        fields = ["id", "type", "description", "road_id", "road_name", "intersection_name",
                  "reported_at", "verified_at", "is_simulated"]


class AdminIncidentSerializer(serializers.ModelSerializer):
    reference = serializers.CharField(read_only=True)
    road_name = serializers.CharField(source="road.name")
    intersection_name = serializers.CharField(source="intersection.name", default=None)
    reviewed_by_name = serializers.SerializerMethodField()
    possible_duplicate_reference = serializers.SerializerMethodField()

    class Meta:
        model = Incident
        fields = ["id", "reference", "type", "description", "status", "road_id", "road_name",
                  "intersection_name", "reported_at", "verified_at", "reporter_name", "reporter_contact",
                  "rejection_reason", "reviewed_by_name", "possible_duplicate_of",
                  "possible_duplicate_reference", "is_simulated"]

    def get_reviewed_by_name(self, obj):
        user = obj.reviewed_by
        return (user.get_full_name() or user.username) if user else None

    def get_possible_duplicate_reference(self, obj):
        return f"KTI-{obj.possible_duplicate_of_id:06d}" if obj.possible_duplicate_of_id else None


class ReportSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=IncidentType.choices)
    road = serializers.PrimaryKeyRelatedField(queryset=Road.objects.all())
    intersection = serializers.PrimaryKeyRelatedField(queryset=Intersection.objects.all(), required=False, allow_null=True)
    description = serializers.CharField(min_length=10, max_length=1000)
    reporter_name = serializers.CharField(max_length=120, required=False, allow_blank=True, default="")
    reporter_contact = serializers.CharField(max_length=160, required=False, allow_blank=True, default="")

    def validate_description(self, value):
        value = " ".join(value.split())
        if len(value) < 10:
            raise serializers.ValidationError("Please describe what you saw in at least 10 characters.")
        return value


class RejectSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=500)

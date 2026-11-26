from rest_framework import serializers

from apps.alerts.models import Alert


class PublicAlertSerializer(serializers.ModelSerializer):
    road_name = serializers.CharField(source="road.name", default=None)

    class Meta:
        model = Alert
        fields = ["id", "message", "trigger_type", "published_at", "road_id", "road_name"]


class AdminAlertSerializer(serializers.ModelSerializer):
    road_name = serializers.CharField(source="road.name", default=None)
    trigger_label = serializers.CharField(source="get_trigger_type_display")
    published_by_name = serializers.SerializerMethodField()
    withdrawn_by_name = serializers.SerializerMethodField()
    incident_status = serializers.CharField(source="incident.status", default=None)

    class Meta:
        model = Alert
        fields = ["id", "message", "trigger_type", "trigger_label", "status", "published_at", "withdrawn_at",
                  "road_id", "road_name", "incident_id", "incident_status", "published_by_name", "withdrawn_by_name"]

    @staticmethod
    def _name(user):
        return (user.get_full_name() or user.username) if user else "System"

    def get_published_by_name(self, obj):
        return self._name(obj.published_by)

    def get_withdrawn_by_name(self, obj):
        return self._name(obj.withdrawn_by) if obj.withdrawn_at else None


class PublishAlertSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=300)
    road = serializers.IntegerField(required=False, allow_null=True)

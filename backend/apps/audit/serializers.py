from rest_framework import serializers

from apps.audit.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    admin_username = serializers.CharField(source="admin.username")
    admin_name = serializers.SerializerMethodField()
    action_label = serializers.CharField(source="get_action_display")

    class Meta:
        model = AuditLog
        fields = ["id", "admin_username", "admin_name", "action", "action_label",
                  "target_type", "target_id", "details", "timestamp"]

    def get_admin_name(self, obj):
        return obj.admin.get_full_name() or obj.admin.username

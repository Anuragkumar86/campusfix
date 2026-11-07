from rest_framework import serializers

from .models import User


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class CurrentUserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="display_name", read_only=True)
    role_label = serializers.CharField(source="get_role_display", read_only=True)
    department = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "name", "first_name", "last_name", "role", "role_label", "department"]

    def get_department(self, obj):
        return {"id": obj.department_id, "name": obj.department.name} if obj.department_id else None


class StaffBriefSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="display_name", read_only=True)

    class Meta:
        model = User
        fields = ["id", "name"]

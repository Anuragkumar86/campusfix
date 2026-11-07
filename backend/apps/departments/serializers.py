from rest_framework import serializers

from .models import Category, Department


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "name", "description"]


class CategorySerializer(serializers.ModelSerializer):
    department = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "description", "department"]

    def get_department(self, obj):
        return {"id": obj.department_id, "name": obj.department.name}

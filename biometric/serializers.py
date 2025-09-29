from rest_framework import serializers
from .models import Employee, PunchLog

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['employee_code', 'name', 'location', 'role', 'card_number', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def validate_employee_code(self, value):
        if not value.strip():
            raise serializers.ValidationError("Employee code cannot be empty")
        return value.strip().upper()

class PunchLogSerializer(serializers.ModelSerializer):
    employee_code = serializers.CharField(source='employee.employee_code', read_only=True)
    employee_name = serializers.CharField(source='employee.name', read_only=True)
    
    class Meta:
        model = PunchLog
        fields = ['id', 'employee_code', 'employee_name', 'punch_time', 'device_name', 'direction', 'raw_data', 'created_at']
        read_only_fields = ['id', 'created_at']

class EmployeeCreateSerializer(serializers.Serializer):
    employee_code = serializers.CharField(max_length=50, required=True)
    name = serializers.CharField(max_length=255, required=True)
    location = serializers.CharField(max_length=100, required=True)
    role = serializers.ChoiceField(choices=Employee.ROLE_CHOICES, default='User')
    verification_type = serializers.CharField(max_length=50, required=False, default='')

class DeviceLogsQuerySerializer(serializers.Serializer):
    location = serializers.CharField(max_length=100, required=True)
    date = serializers.DateField(required=True)

class EmployeeLogsQuerySerializer(serializers.Serializer):
    date = serializers.DateField(required=True)
from django.contrib import admin
from .models import Employee, PunchLog

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['employee_code', 'name', 'location', 'role', 'created_at']
    list_filter = ['location', 'role', 'created_at']
    search_fields = ['employee_code', 'name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(PunchLog)
class PunchLogAdmin(admin.ModelAdmin):
    list_display = ['employee', 'punch_time', 'device_name', 'direction']
    list_filter = ['device_name', 'direction', 'punch_time']
    search_fields = ['employee__employee_code', 'employee__name']
    readonly_fields = ['created_at']
    date_hierarchy = 'punch_time'
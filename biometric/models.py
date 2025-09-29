from django.db import models
from django.core.exceptions import ValidationError

class Employee(models.Model):
    ROLE_CHOICES = [
        ('User', 'User'),
        ('Admin', 'Admin'),
        ('Supervisor', 'Supervisor'),
    ]
    
    employee_code = models.CharField(max_length=50, unique=True, verbose_name='Employee Code')
    name = models.CharField(max_length=255, verbose_name='Full Name')
    location = models.CharField(max_length=100, verbose_name='Location')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='User', verbose_name='Role')
    card_number = models.CharField(max_length=50, null=True, blank=True, verbose_name='Card Number')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'biometric_employees'
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'
        indexes = [
            models.Index(fields=['employee_code']),
            models.Index(fields=['location']),
        ]
    
    def __str__(self):
        return f"{self.employee_code} - {self.name}"

class PunchLog(models.Model):
    DIRECTION_CHOICES = [
        ('IN', 'Check In'),
        ('OUT', 'Check Out'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='punch_logs')
    punch_time = models.DateTimeField(verbose_name='Punch Time')
    device_name = models.CharField(max_length=100, verbose_name='Device Name')
    direction = models.CharField(max_length=3, choices=DIRECTION_CHOICES, verbose_name='Direction')
    raw_data = models.JSONField(default=dict, verbose_name='Raw Data')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'biometric_punch_logs'
        verbose_name = 'Punch Log'
        verbose_name_plural = 'Punch Logs'
        indexes = [
            models.Index(fields=['punch_time']),
            models.Index(fields=['employee', 'punch_time']),
            models.Index(fields=['device_name']),
        ]
        ordering = ['-punch_time']
    
    def __str__(self):
        return f"{self.employee.employee_code} - {self.punch_time} - {self.direction}"
    
    def clean(self):
        if self.punch_time and self.punch_time.year < 2000:
            raise ValidationError('Invalid punch time')
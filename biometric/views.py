import logging
from datetime import datetime

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Employee, PunchLog
from .serializers import (
    EmployeeSerializer, 
    PunchLogSerializer,
    EmployeeCreateSerializer,
    DeviceLogsQuerySerializer,
    EmployeeLogsQuerySerializer
)
from .services.ebio import EBioServerClient

logger = logging.getLogger(__name__)

class EmployeeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing employees and their biometric data
    """
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Create employee in local database and sync with biometric device
        """
        create_serializer = EmployeeCreateSerializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)
        
        # Check if employee already exists
        emp_code = create_serializer.validated_data['employee_code']
        if Employee.objects.filter(employee_code=emp_code).exists():
            return Response(
                {'error': f'Employee {emp_code} already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Sync with biometric device
        ebio_client = EBioServerClient()
        sync_result = ebio_client.update_employee(
            emp_code=emp_code,
            emp_name=create_serializer.validated_data['name'],
            emp_location=create_serializer.validated_data['location'],
            emp_role=create_serializer.validated_data.get('role', 'User'),
            verification_type=create_serializer.validated_data.get('verification_type', '')
        )
        
        if not sync_result['success']:
            return Response(
                {'error': f'Failed to sync with biometric device: {sync_result["error"]}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Create local employee record
        employee_data = {
            'employee_code': emp_code,
            'name': create_serializer.validated_data['name'],
            'location': create_serializer.validated_data['location'],
            'role': create_serializer.validated_data.get('role', 'User'),
        }
        
        serializer = self.get_serializer(data=employee_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                **serializer.data,
                'biometric_sync': sync_result
            },
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete employee from local database and biometric device
        """
        employee = self.get_object()
        emp_code = employee.employee_code
        
        # Delete from biometric device first
        ebio_client = EBioServerClient()
        delete_result = ebio_client.delete_employee(emp_code)
        
        if not delete_result['success']:
            logger.warning(f"Failed to delete employee {emp_code} from biometric device: {delete_result['error']}")
            # Continue with local deletion even if biometric deletion fails
        
        # Delete from local database
        self.perform_destroy(employee)
        
        return Response(
            {
                'message': f'Employee {emp_code} deleted successfully',
                'biometric_sync': delete_result
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        """
        Get employee details from biometric device
        """
        employee = self.get_object()
        ebio_client = EBioServerClient()
        result = ebio_client.get_employee_details(employee.employee_code)
        
        return Response(result)
    
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """
        Get employee punch logs for a specific date
        """
        employee = self.get_object()
        
        query_serializer = EmployeeLogsQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        
        date = query_serializer.validated_data['date']
        ebio_client = EBioServerClient()
        result = ebio_client.get_employee_punch_logs(
            employee.employee_code,
            date.strftime('%Y-%m-%d')
        )
        
        return Response(result)

class DeviceViewSet(viewsets.ViewSet):
    """
    ViewSet for device-related operations
    """
    
    def list(self, request):
        """
        Get list of devices for a location
        """
        location = request.query_params.get('location')
        if not location:
            raise ValidationError({'error': 'Location parameter is required'})
        
        ebio_client = EBioServerClient()
        result = ebio_client.get_device_list(location)
        
        return Response(result)
    
    @action(detail=False, methods=['get'])
    def logs(self, request):
        """
        Get device logs for a location and date
        """
        query_serializer = DeviceLogsQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        
        location = query_serializer.validated_data['location']
        date = query_serializer.validated_data['date']
        
        ebio_client = EBioServerClient()
        result = ebio_client.get_device_logs(
            location,
            date.strftime('%Y-%m-%d')
        )
        
        return Response(result)
    
    @action(detail=False, methods=['get'])
    def illegal(self, request):
        """
        Get illegal/cardless logs for a location and date
        """
        query_serializer = DeviceLogsQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        
        location = query_serializer.validated_data['location']
        date = query_serializer.validated_data['date']
        
        ebio_client = EBioServerClient()
        result = ebio_client.get_device_illegal_logs(
            location,
            date.strftime('%Y-%m-%d')
        )
        
        return Response(result)

class PunchLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing punch logs
    """
    queryset = PunchLog.objects.all()
    serializer_class = PunchLogSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by employee code if provided
        employee_code = self.request.query_params.get('employee_code')
        if employee_code:
            queryset = queryset.filter(employee__employee_code=employee_code)
        
        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(punch_time__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(punch_time__date__lte=end_date)
        
        return queryset.select_related('employee')
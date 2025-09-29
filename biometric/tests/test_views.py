from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from biometric.models import Employee
from unittest.mock import patch

class EmployeeViewSetTests(APITestCase):
    
    def setUp(self):
        self.employee_data = {
            'employee_code': 'EMP001',
            'name': 'John Doe',
            'location': 'Main Office',
            'role': 'User'
        }
    
    @patch('biometric.views.EBioServerClient')
    def test_create_employee_success(self, mock_ebio_client):
        mock_client_instance = mock_ebio_client.return_value
        mock_client_instance.update_employee.return_value = {
            'success': True,
            'message': 'Employee updated successfully'
        }
        
        response = self.client.post(
            reverse('employee-list'),
            data=self.employee_data
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Employee.objects.count(), 1)
        self.assertEqual(Employee.objects.first().employee_code, 'EMP001')
    
    @patch('biometric.views.EBioServerClient')
    def test_create_employee_biometric_failure(self, mock_ebio_client):
        mock_client_instance = mock_ebio_client.return_value
        mock_client_instance.update_employee.return_value = {
            'success': False,
            'error': 'SOAP Fault'
        }
        
        response = self.client.post(
            reverse('employee-list'),
            data=self.employee_data
        )
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(Employee.objects.count(), 0)
    
    def test_create_employee_duplicate(self):
        Employee.objects.create(**self.employee_data)
        
        response = self.client.post(
            reverse('employee-list'),
            data=self.employee_data
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    @patch('biometric.views.EBioServerClient')
    def test_delete_employee(self, mock_ebio_client):
        employee = Employee.objects.create(**self.employee_data)
        
        mock_client_instance = mock_ebio_client.return_value
        mock_client_instance.delete_employee.return_value = {
            'success': True,
            'message': 'Employee deleted successfully'
        }
        
        response = self.client.delete(
            reverse('employee-detail', args=[employee.id])
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Employee.objects.count(), 0)

class DeviceViewSetTests(APITestCase):
    
    @patch('biometric.views.EBioServerClient')
    def test_get_device_list(self, mock_ebio_client):
        mock_client_instance = mock_ebio_client.return_value
        mock_client_instance.get_device_list.return_value = {
            'success': True,
            'devices': [{'name': 'Device001'}],
            'count': 1
        }
        
        response = self.client.get(
            reverse('device-list') + '?location=Main%20Office'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('devices', response.data)
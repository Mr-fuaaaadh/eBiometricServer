from unittest.mock import Mock, patch
from django.test import TestCase
from biometric.services.ebio import EBioServerClient
from django.conf import settings

class EBioServerClientTests(TestCase):
    
    def setUp(self):
        self.client = EBioServerClient()
        self.client.client = Mock()
        self.client.client.service = Mock()
    
    @patch('biometric.services.ebio.settings')
    def test_update_employee_success(self, mock_settings):
        # Mock SOAP response
        mock_settings.EBIO_USERNAME = 'test_user'
        mock_settings.EBIO_PASSWORD = 'test_pass'
        
        self.client.client.service.UpdateEmployee.return_value = "Employee updated successfully"
        
        result = self.client.update_employee(
            emp_code='EMP001',
            emp_name='John Doe',
            emp_location='Main Office',
            emp_role='User',
            verification_type=''
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['employee_code'], 'EMP001')
        self.client.client.service.UpdateEmployee.assert_called_once()
    
    @patch('biometric.services.ebio.settings')
    def test_update_employee_failure(self, mock_settings):
        mock_settings.EBIO_USERNAME = 'test_user'
        mock_settings.EBIO_PASSWORD = 'test_pass'
        
        self.client.client.service.UpdateEmployee.side_effect = Exception("SOAP Fault")
        
        result = self.client.update_employee(
            emp_code='EMP001',
            emp_name='John Doe',
            emp_location='Main Office'
        )
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    @patch('biometric.services.ebio.settings')
    def test_get_employee_details(self, mock_settings):
        mock_settings.EBIO_USERNAME = 'test_user'
        mock_settings.EBIO_PASSWORD = 'test_pass'
        
        mock_response = Mock()
        mock_response.EmployeeCode = 'EMP001'
        mock_response.EmployeeName = 'John Doe'
        self.client.client.service.GetEmployeeDetails.return_value = mock_response
        
        result = self.client.get_employee_details('EMP001')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['employee_code'], 'EMP001')
        self.assertIn('details', result)
    
    @patch('biometric.services.ebio.settings')
    def test_get_device_list(self, mock_settings):
        mock_settings.EBIO_USERNAME = 'test_user'
        mock_settings.EBIO_PASSWORD = 'test_pass'
        
        mock_device = Mock()
        mock_device.DeviceName = 'Device001'
        mock_device.Location = 'Main Office'
        self.client.client.service.GetDeviceList.return_value = [mock_device]
        
        result = self.client.get_device_list('Main Office')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['location'], 'Main Office')
        self.assertIn('devices', result)
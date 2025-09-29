import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

import zeep
from zeep import Client
from zeep.transports import Transport
from requests import Session, RequestException
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

class EBioServerClient:
    """
    Client for eSSL Biometric eBioServerNew SOAP Web Service
    """
    
    def __init__(self):
        self.wsdl_url = settings.EBIO_SERVER_URL
        self.username = settings.EBIO_USERNAME
        self.password = settings.EBIO_PASSWORD
        self.client = None
        self._connect()
    
    def _connect(self, retries: int = 3) -> None:
        """
        Establish connection to SOAP service with retry logic
        """
        session = Session()
        session.verify = False  # For self-signed certificates
        
        transport = Transport(session=session, operation_timeout=30)
        
        for attempt in range(retries):
            try:
                self.client = Client(self.wsdl_url, transport=transport)
                logger.info(f"Successfully connected to eBioServer (attempt {attempt + 1})")
                break
            except RequestException as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {str(e)}")
                if attempt == retries - 1:
                    logger.error(f"Failed to connect to eBioServer after {retries} attempts")
                    raise
    
    def _make_request(self, service_method: str, *args) -> Any:
        """
        Make SOAP request with error handling and automatic reconnection
        """
        try:
            service = self.client.service
            method = getattr(service, service_method)
            result = method(*args)
            logger.debug(f"SOAP request {service_method} completed successfully")
            return result
        except zeep.exceptions.Fault as fault:
            logger.error(f"SOAP Fault in {service_method}: {fault.message}")
            raise
        except RequestException as e:
            logger.error(f"Network error in {service_method}: {str(e)}")
            # Try to reconnect and retry once
            try:
                self._connect(retries=1)
                service = self.client.service
                method = getattr(service, service_method)
                return method(*args)
            except Exception as retry_error:
                logger.error(f"Retry failed for {service_method}: {str(retry_error)}")
                raise
    
    def update_employee(self, emp_code: str, emp_name: str, emp_location: str, 
                       emp_role: str = "User", verification_type: str = "") -> Dict[str, Any]:
        """
        Add or update employee in biometric device
        """
        try:
            result = self._make_request(
                'UpdateEmployee',
                self.username,
                self.password,
                emp_code,
                emp_name,
                emp_location,
                emp_role,
                verification_type
            )
            
            return {
                'success': True,
                'employee_code': emp_code,
                'message': result if isinstance(result, str) else 'Employee updated successfully',
                'timestamp': timezone.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to update employee {emp_code}: {str(e)}")
            return {
                'success': False,
                'employee_code': emp_code,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }
    
    def get_employee_details(self, emp_code: str) -> Dict[str, Any]:
        """
        Get employee details from biometric system
        """
        try:
            result = self._make_request(
                'GetEmployeeDetails',
                self.username,
                self.password,
                emp_code
            )
            
            # Parse the result based on expected SOAP response structure
            return {
                'success': True,
                'employee_code': emp_code,
                'details': self._parse_soap_response(result),
                'timestamp': timezone.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get employee details for {emp_code}: {str(e)}")
            return {
                'success': False,
                'employee_code': emp_code,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }
    
    def get_employee_punch_logs(self, emp_code: str, attendance_date: str) -> Dict[str, Any]:
        """
        Get employee punch logs for a specific date
        """
        try:
            result = self._make_request(
                'GetEmployeePunchLogs',
                self.username,
                self.password,
                emp_code,
                attendance_date
            )
            
            logs = self._parse_punch_logs(result)
            return {
                'success': True,
                'employee_code': emp_code,
                'date': attendance_date,
                'logs': logs,
                'count': len(logs),
                'timestamp': timezone.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get punch logs for {emp_code} on {attendance_date}: {str(e)}")
            return {
                'success': False,
                'employee_code': emp_code,
                'date': attendance_date,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }
    
    def delete_employee(self, emp_code: str) -> Dict[str, Any]:
        """
        Delete employee from biometric system
        """
        try:
            result = self._make_request(
                'DeleteEmployee',
                self.username,
                self.password,
                emp_code
            )
            
            return {
                'success': True,
                'employee_code': emp_code,
                'message': result if isinstance(result, str) else 'Employee deleted successfully',
                'timestamp': timezone.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to delete employee {emp_code}: {str(e)}")
            return {
                'success': False,
                'employee_code': emp_code,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }
    
    def get_device_list(self, location: str) -> Dict[str, Any]:
        """
        Get list of devices for a location
        """
        try:
            result = self._make_request(
                'GetDeviceList',
                self.username,
                self.password,
                location
            )
            
            devices = self._parse_device_list(result)
            return {
                'success': True,
                'location': location,
                'devices': devices,
                'count': len(devices),
                'timestamp': timezone.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get device list for {location}: {str(e)}")
            return {
                'success': False,
                'location': location,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }
    
    def get_device_logs(self, location: str, log_date: str) -> Dict[str, Any]:
        """
        Get device logs for a specific location and date
        """
        try:
            result = self._make_request(
                'GetDeviceLogs',
                self.username,
                self.password,
                location,
                log_date
            )
            
            logs = self._parse_device_logs(result)
            return {
                'success': True,
                'location': location,
                'date': log_date,
                'logs': logs,
                'count': len(logs),
                'timestamp': timezone.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get device logs for {location} on {log_date}: {str(e)}")
            return {
                'success': False,
                'location': location,
                'date': log_date,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }
    
    def get_device_illegal_logs(self, location: str, log_date: str) -> Dict[str, Any]:
        """
        Get illegal/cardless logs for a specific location and date
        """
        try:
            result = self._make_request(
                'GetDeviceIllegalLogs',
                self.username,
                self.password,
                location,
                log_date
            )
            
            logs = self._parse_device_logs(result)
            return {
                'success': True,
                'location': location,
                'date': log_date,
                'logs': logs,
                'count': len(logs),
                'timestamp': timezone.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get illegal logs for {location} on {log_date}: {str(e)}")
            return {
                'success': False,
                'location': location,
                'date': log_date,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }
    
    def _parse_soap_response(self, response) -> Any:
        """
        Parse SOAP response to Python native types
        """
        if hasattr(response, '__dict__'):
            return {k: v for k, v in response.__dict__.items() if not k.startswith('_')}
        elif isinstance(response, (str, int, float, bool)):
            return response
        else:
            return str(response)
    
    def _parse_punch_logs(self, response) -> List[Dict]:
        """
        Parse punch logs from SOAP response
        """
        logs = []
        if isinstance(response, list):
            for log in response:
                if hasattr(log, '__dict__'):
                    logs.append(self._parse_soap_response(log))
                else:
                    logs.append({'raw_data': str(log)})
        elif response:
            logs.append(self._parse_soap_response(response))
        
        return logs
    
    def _parse_device_list(self, response) -> List[Dict]:
        """
        Parse device list from SOAP response
        """
        devices = []
        if isinstance(response, list):
            for device in response:
                if hasattr(device, '__dict__'):
                    devices.append(self._parse_soap_response(device))
                else:
                    devices.append({'name': str(device)})
        elif response:
            devices.append(self._parse_soap_response(response))
        
        return devices
    
    def _parse_device_logs(self, response) -> List[Dict]:
        """
        Parse device logs from SOAP response
        """
        return self._parse_punch_logs(response)
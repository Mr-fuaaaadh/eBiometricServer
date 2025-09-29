from django.core.management.base import BaseCommand
from django.utils import timezone
from biometric.services.ebio import EBioServerClient
from biometric.models import Employee, PunchLog
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sync attendance data from biometric devices'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--location',
            type=str,
            required=True,
            help='Location to sync attendance for'
        )
        parser.add_argument(
            '--date',
            type=str,
            help='Date to sync (YYYY-MM-DD), defaults to today'
        )
    
    def handle(self, *args, **options):
        location = options['location']
        date = options.get('date') or timezone.now().date().strftime('%Y-%m-%d')
        
        self.stdout.write(f"Syncing attendance for {location} on {date}")
        
        ebio_client = EBioServerClient()
        
        # Get device logs
        result = ebio_client.get_device_logs(location, date)
        
        if result['success']:
            self._process_logs(result['logs'], location)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully processed {len(result['logs'])} logs for {location}"
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(f"Failed to sync logs: {result['error']}")
            )
    
    def _process_logs(self, logs, location):
        """
        Process and store logs in database
        """
        for log in logs:
            try:
                # Extract employee code from log data
                emp_code = log.get('EmployeeCode') or log.get('emp_code')
                if not emp_code:
                    continue
                
                # Get or create employee
                employee, created = Employee.objects.get_or_create(
                    employee_code=emp_code,
                    defaults={
                        'name': log.get('EmployeeName', 'Unknown'),
                        'location': location,
                        'role': 'User'
                    }
                )
                
                # Create punch log
                punch_time_str = log.get('PunchTime') or log.get('punch_time')
                if punch_time_str:
                    # Parse punch time - adjust format based on actual SOAP response
                    punch_time = timezone.make_aware(
                        timezone.datetime.strptime(punch_time_str, '%Y-%m-%d %H:%M:%S')
                    )
                    
                    PunchLog.objects.get_or_create(
                        employee=employee,
                        punch_time=punch_time,
                        defaults={
                            'device_name': log.get('DeviceName', 'Unknown'),
                            'direction': log.get('Direction', 'IN'),
                            'raw_data': log
                        }
                    )
                
            except Exception as e:
                logger.error(f"Error processing log {log}: {str(e)}")
                continue
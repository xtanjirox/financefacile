from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from accounts.models import Company
from core.models import CalendarEvent
from datetime import timedelta

class Command(BaseCommand):
    help = 'Seed the database with sample calendar events'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Get the first company and user
        try:
            company = Company.objects.first()
            user = User.objects.first()
            
            if not company or not user:
                self.stdout.write(self.style.ERROR('No company or user found. Please create them first.'))
                return
                
            # Clear existing events
            CalendarEvent.objects.all().delete()
            
            # Create sample events
            now = timezone.now()
            
            # Today's event
            CalendarEvent.objects.create(
                company=company,
                title='Team Meeting',
                description='Weekly team sync',
                start_date=now.replace(hour=10, minute=0, second=0, microsecond=0),
                end_date=now.replace(hour=11, minute=0, second=0, microsecond=0),
                theme='primary',
                created_by=user
            )
            
            # Tomorrow's event (all day)
            CalendarEvent.objects.create(
                company=company,
                title='Product Launch',
                description='Launch of new product',
                start_date=(now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0),
                end_date=(now + timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=0),
                all_day=True,
                theme='success',
                created_by=user
            )
            
            # Event in 3 days
            CalendarEvent.objects.create(
                company=company,
                title='Client Call',
                description='Monthly client check-in',
                start_date=(now + timedelta(days=3)).replace(hour=14, minute=30, second=0, microsecond=0),
                end_date=(now + timedelta(days=3)).replace(hour=15, minute=15, second=0, microsecond=0),
                theme='info',
                created_by=user
            )
            
            # Multi-day event
            CalendarEvent.objects.create(
                company=company,
                title='Conference',
                description='Annual developer conference',
                start_date=(now + timedelta(days=5)).replace(hour=9, minute=0, second=0, microsecond=0),
                end_date=(now + timedelta(days=7)).replace(hour=18, minute=0, second=0, microsecond=0),
                theme='warning',
                created_by=user
            )
            
            self.stdout.write(self.style.SUCCESS('Successfully created sample calendar events!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating sample events: {str(e)}'))

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import CalendarEvent
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates sample calendar events for demonstration purposes'

    def handle(self, *args, **options):
        # Get the first user in the system
        try:
            user = User.objects.first()
            if not user:
                self.stdout.write(self.style.ERROR('No users found in the system. Please create a user first.'))
                return
                
            # Get the user's company
            company = None
            if hasattr(user, 'profile') and hasattr(user.profile, 'company'):
                company = user.profile.company
            
            if not company:
                self.stdout.write(self.style.ERROR('No company found for the user. Please set up a company first.'))
                return
                
            # Delete existing events (optional)
            # CalendarEvent.objects.all().delete()
            
            # Get current date
            now = timezone.now()
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Create events for today
            events_data = [
                {
                    'title': 'Client Meeting',
                    'description': 'Discuss project requirements with client',
                    'start_date': today.replace(hour=10, minute=0),
                    'end_date': today.replace(hour=11, minute=30),
                    'all_day': False,
                    'theme': 'primary'
                },
                {
                    'title': 'Team Standup',
                    'description': 'Daily team standup meeting',
                    'start_date': today.replace(hour=9, minute=0),
                    'end_date': today.replace(hour=9, minute=30),
                    'all_day': False,
                    'theme': 'info'
                },
                {
                    'title': 'Project Deadline',
                    'description': 'Final submission for project X',
                    'start_date': today.replace(hour=17, minute=0),
                    'end_date': today.replace(hour=18, minute=0),
                    'all_day': False,
                    'theme': 'danger'
                },
                {
                    'title': 'Lunch with Partners',
                    'description': 'Business lunch with potential partners',
                    'start_date': today.replace(hour=12, minute=30),
                    'end_date': today.replace(hour=14, minute=0),
                    'all_day': False,
                    'theme': 'success'
                },
            ]
            
            # Create events for tomorrow
            tomorrow = today + timedelta(days=1)
            events_data.extend([
                {
                    'title': 'Marketing Review',
                    'description': 'Review marketing campaign results',
                    'start_date': tomorrow.replace(hour=11, minute=0),
                    'end_date': tomorrow.replace(hour=12, minute=0),
                    'all_day': False,
                    'theme': 'warning'
                },
                {
                    'title': 'Budget Planning',
                    'description': 'Quarterly budget planning session',
                    'start_date': tomorrow.replace(hour=14, minute=0),
                    'end_date': tomorrow.replace(hour=16, minute=0),
                    'all_day': False,
                    'theme': 'secondary'
                },
                {
                    'title': 'Staff Training',
                    'description': 'Training session for new software',
                    'start_date': tomorrow,
                    'end_date': tomorrow + timedelta(days=1),
                    'all_day': True,
                    'theme': 'info'
                },
            ])
            
            # Create events for next week
            next_week = today + timedelta(days=7)
            events_data.extend([
                {
                    'title': 'Annual Conference',
                    'description': 'Industry annual conference',
                    'start_date': next_week,
                    'end_date': next_week + timedelta(days=3),
                    'all_day': True,
                    'theme': 'primary'
                },
            ])
            
            # Create the events
            created_count = 0
            for event_data in events_data:
                event, created = CalendarEvent.objects.get_or_create(
                    title=event_data['title'],
                    start_date=event_data['start_date'],
                    defaults={
                        'description': event_data['description'],
                        'end_date': event_data['end_date'],
                        'all_day': event_data['all_day'],
                        'theme': event_data['theme'],
                        'company': company,
                        'created_by': user
                    }
                )
                if created:
                    created_count += 1
            
            self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} sample calendar events'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating sample events: {str(e)}'))

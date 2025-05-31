import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from core.models import CalendarEvent
from accounts.models import Company

User = get_user_model()

class Command(BaseCommand):
    help = 'Add sample calendar events for testing'

    def handle(self, *args, **options):
        # Get the first company and admin user
        try:
            company = Company.objects.first()
            if not company:
                self.stdout.write(self.style.ERROR('No company found. Please create a company first.'))
                return
                
            admin_user = User.objects.filter(is_staff=True).first()
            if not admin_user:
                self.stdout.write(self.style.ERROR('No admin user found.'))
                return
                
            # Define event themes
            themes = ['primary', 'secondary', 'success', 'info', 'warning', 'danger', 'dark']
            
            # Define sample event titles
            event_titles = [
                'Réunion avec client',
                'Présentation de projet',
                'Paiement de facture',
                'Échéance fiscale',
                'Entretien avec fournisseur',
                'Révision comptable',
                'Formation équipe',
                'Lancement de produit',
                'Maintenance système',
                'Audit interne'
            ]
            
            # Get current date
            now = timezone.now()
            
            # Create 15 sample events
            events_created = 0
            for i in range(15):
                # Random date within next 60 days
                days_offset = random.randint(1, 60)
                start_date = now + timedelta(days=days_offset)
                
                # 30% chance of all-day event
                all_day = random.random() < 0.3
                
                if all_day:
                    # All-day event
                    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    end_date = start_date + timedelta(days=random.randint(1, 3))
                else:
                    # Timed event
                    start_date = start_date.replace(
                        hour=random.randint(8, 17),
                        minute=random.choice([0, 15, 30, 45]),
                        second=0,
                        microsecond=0
                    )
                    # Duration between 30 minutes and 3 hours
                    duration_minutes = random.choice([30, 45, 60, 90, 120, 180])
                    end_date = start_date + timedelta(minutes=duration_minutes)
                
                # Create the event
                title = random.choice(event_titles)
                description = f"Description détaillée pour l'événement '{title}' #{i+1}"
                theme = random.choice(themes)
                
                CalendarEvent.objects.create(
                    company=company,
                    title=title,
                    description=description,
                    start_date=start_date,
                    end_date=end_date,
                    all_day=all_day,
                    theme=theme,
                    created_by=admin_user
                )
                events_created += 1
            
            self.stdout.write(self.style.SUCCESS(f'Successfully created {events_created} sample calendar events'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating sample events: {e}'))

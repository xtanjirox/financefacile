from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from core.notifications import Notification
from core.models import Product, Invoice, Expense, CalendarEvent


class Command(BaseCommand):
    help = 'Creates test notifications for development purposes'

    def handle(self, *args, **options):
        # Get the first user as recipient
        try:
            user = User.objects.first()
            if not user:
                self.stdout.write(self.style.ERROR('No users found in the database'))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error getting user: {e}'))
            return

        # Create test notifications
        self._create_test_notifications(user)
        
        self.stdout.write(self.style.SUCCESS('Successfully created test notifications'))

    def _create_test_notifications(self, user):
        """Create various test notifications for the user"""
        # Create a system notification
        Notification.objects.create(
            recipient=user,
            notification_type='system',
            title='Welcome to FinanceFacile',
            message='Welcome to the new notification system! You can now receive alerts for important events.',
            is_read=False
        )
        
        # Create an event invitation notification
        try:
            event = CalendarEvent.objects.first()
            if event:
                content_type = ContentType.objects.get_for_model(event)
                Notification.objects.create(
                    recipient=user,
                    notification_type='event_invite',
                    title=f'New Calendar Event: {event.title}',
                    message=f'You have been added to an event: {event.title} starting on {event.start_date.strftime("%Y-%m-%d %H:%M")}',
                    content_type=content_type,
                    object_id=event.id,
                    is_read=False
                )
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Could not create event notification: {e}'))
        
        # Create a low stock notification
        try:
            product = Product.objects.first()
            if product:
                content_type = ContentType.objects.get_for_model(product)
                Notification.objects.create(
                    recipient=user,
                    notification_type='low_stock',
                    title=f'Low Stock Alert: {product.name}',
                    message=f'Product {product.name} ({product.sku}) is running low on stock. Current quantity: {product.quantity}',
                    content_type=content_type,
                    object_id=product.id,
                    is_read=False
                )
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Could not create product notification: {e}'))
        
        # Create an invoice notification
        try:
            invoice = Invoice.objects.first()
            if invoice:
                content_type = ContentType.objects.get_for_model(invoice)
                Notification.objects.create(
                    recipient=user,
                    notification_type='invoice_created',
                    title='New Invoice Created',
                    message=f'Invoice #{invoice.id} has been created',
                    content_type=content_type,
                    object_id=invoice.id,
                    is_read=False
                )
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Could not create invoice notification: {e}'))
        
        # Create an expense notification
        try:
            expense = Expense.objects.first()
            if expense:
                content_type = ContentType.objects.get_for_model(expense)
                Notification.objects.create(
                    recipient=user,
                    notification_type='expense_created',
                    title='New Expense Recorded',
                    message=f'Expense of {expense.amount} for {expense.category.name} has been recorded',
                    content_type=content_type,
                    object_id=expense.id,
                    is_read=False
                )
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Could not create expense notification: {e}'))

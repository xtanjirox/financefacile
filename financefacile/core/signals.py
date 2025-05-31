from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from accounts.models import Company
from core.models import ProductCategory, Product, Invoice, Expense, CalendarEvent
from .notifications import Notification

@receiver(post_save, sender=Company)
def create_uncategorized_category(sender, instance, created, **kwargs):
    """
    Create an 'Uncategorized' product category for each new company
    """
    if created:
        # Check if the company already has an 'Uncategorized' category
        uncategorized_exists = ProductCategory.objects.filter(
            company=instance, 
            name='Uncategorized'
        ).exists()
        
        if not uncategorized_exists:
            # Create the 'Uncategorized' category for this company
            ProductCategory.objects.create(
                company=instance,
                name='Uncategorized',
                parent=None  # This is a top-level category
            )


# Calendar Event Notifications
@receiver(m2m_changed, sender=CalendarEvent.participants.through)
def notify_event_participants(sender, instance, action, pk_set, **kwargs):
    """
    Send notifications to users when they are added to a calendar event
    """
    if action == 'post_add' and pk_set:
        event = instance
        content_type = ContentType.objects.get_for_model(event)
        
        # Notify each added participant
        for user_id in pk_set:
            user = User.objects.get(id=user_id)
            
            # Create notification
            Notification.objects.create(
                recipient=user,
                notification_type='event_invite',
                title=f'New Calendar Event: {event.title}',
                message=f'You have been added to an event: {event.title} starting on {event.start_date.strftime("%Y-%m-%d %H:%M")}',
                content_type=content_type,
                object_id=event.id
            )


# Product Low Stock Notification
@receiver(post_save, sender=Product)
def notify_low_stock(sender, instance, **kwargs):
    """
    Send notifications to admin users when a product's stock is low (less than 5)
    """
    if instance.quantity < 5 and not instance.is_archived:
        content_type = ContentType.objects.get_for_model(instance)
        
        # Get admin users from the company
        admin_users = User.objects.filter(
            profile__company=instance.company,
            profile__is_company_admin=True
        )
        
        for admin in admin_users:
            # Check if a similar notification already exists and is unread
            existing_notification = Notification.objects.filter(
                recipient=admin,
                notification_type='low_stock',
                object_id=instance.id,
                content_type=content_type,
                is_read=False
            ).exists()
            
            if not existing_notification:
                Notification.objects.create(
                    recipient=admin,
                    notification_type='low_stock',
                    title=f'Low Stock Alert: {instance.name}',
                    message=f'Product {instance.name} ({instance.sku}) is running low on stock. Current quantity: {instance.quantity}',
                    content_type=content_type,
                    object_id=instance.id
                )


# Invoice Creation Notification
@receiver(post_save, sender=Invoice)
def notify_invoice_created(sender, instance, created, **kwargs):
    """
    Send notifications to admin users when a new invoice is created
    """
    if created:
        content_type = ContentType.objects.get_for_model(instance)
        
        # Get admin users from the company
        admin_users = User.objects.filter(
            profile__company=instance.company,
            profile__is_company_admin=True
        )
        
        for admin in admin_users:
            # Don't notify the creator
            if admin != instance.created_by:
                Notification.objects.create(
                    recipient=admin,
                    notification_type='invoice_created',
                    title='New Invoice Created',
                    message=f'Invoice #{instance.id} has been created by {instance.created_by.get_full_name() or instance.created_by.username}',
                    content_type=content_type,
                    object_id=instance.id
                )


# Expense Creation Notification
@receiver(post_save, sender=Expense)
def notify_expense_created(sender, instance, created, **kwargs):
    """
    Send notifications to admin users when a new expense is created
    """
    if created:
        content_type = ContentType.objects.get_for_model(instance)
        
        # Get admin users from the company
        admin_users = User.objects.filter(
            profile__company=instance.company,
            profile__is_company_admin=True
        )
        
        for admin in admin_users:
            # Don't notify the creator
            if admin != instance.created_by:
                Notification.objects.create(
                    recipient=admin,
                    notification_type='expense_created',
                    title='New Expense Recorded',
                    message=f'Expense of {instance.amount} for {instance.category.name} has been recorded by {instance.created_by.get_full_name() or instance.created_by.username}',
                    content_type=content_type,
                    object_id=instance.id
                )

from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.urls import reverse

class Notification(models.Model):
    """
    A notification model to handle system notifications for users.
    """
    NOTIFICATION_TYPES = (
        ('event_invite', 'Event Invitation'),
        ('low_stock', 'Low Stock Alert'),
        ('invoice_created', 'Invoice Created'),
        ('expense_created', 'Expense Created'),
        ('system', 'System Notification'),
    )
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # For linking to specific objects (Product, Invoice, Event, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.recipient.username} - {self.title}"
        
    def mark_as_read(self):
        """
        Mark the notification as read and save it
        """
        self.is_read = True
        self.save()
        
    def get_absolute_url(self):
        """
        Returns the URL to the related object if available
        """
        if not self.content_object:
            return '#'
            
        if hasattr(self.content_object, 'get_absolute_url'):
            return self.content_object.get_absolute_url()
            
        # Default URLs based on notification type
        if self.notification_type == 'event_invite':
            return reverse('calendar-event-detail', kwargs={'pk': self.object_id})
        elif self.notification_type == 'low_stock':
            return reverse('product-detail', kwargs={'pk': self.object_id})
        elif self.notification_type == 'invoice_created':
            return reverse('invoice-detail', kwargs={'pk': self.object_id})
        elif self.notification_type == 'expense_created':
            return reverse('expense-detail', kwargs={'pk': self.object_id})
        
        return '#'

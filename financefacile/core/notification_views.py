from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import get_object_or_404, redirect

from .notifications import Notification

@ensure_csrf_cookie
def get_user_notifications(request):
    """
    API endpoint to get the current user's notifications
    """
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return JsonResponse({
            'error': 'Authentication required',
            'status': 'error'
        }, status=403)
    
    try:
        # Get unread notifications first, then read ones, limited to 10 total
        unread_notifications = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).order_by('-created_at')
        
        read_notifications = Notification.objects.filter(
            recipient=request.user,
            is_read=True
        ).order_by('-created_at')[:5]  # Limit to 5 read notifications
        
        # Combine the notifications
        notifications = list(unread_notifications) + list(read_notifications)
        
        # Format the notifications for JSON response
        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                'id': notification.id,
                'type': notification.notification_type,
                'title': notification.title,
                'message': notification.message,
                'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M'),
                'is_read': notification.is_read,
                'url': notification.get_absolute_url()
            })
        
        # Get the count of unread notifications
        unread_count = unread_notifications.count()
        
        return JsonResponse({
            'notifications': notifications_data,
            'unread_count': unread_count,
            'status': 'success'
        })
    except Exception as e:
        # Log the error
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching notifications: {str(e)}")
        
        # Return error response
        return JsonResponse({
            'error': 'Could not retrieve notifications',
            'status': 'error'
        }, status=500)

@login_required
@require_http_methods(["POST"])
def mark_notification_read(request, notification_id):
    """
    Mark a notification as read and redirect to its URL
    """
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    
    # Mark as read if not already
    if not notification.is_read:
        notification.is_read = True
        notification.save()
    
    # Return JSON response if requested via AJAX, otherwise redirect
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'message': 'Notification marked as read',
            'url': notification.get_absolute_url()
        })
    
    # Redirect to the notification's URL for non-AJAX requests
    return redirect(notification.get_absolute_url())

@login_required
@require_http_methods(["POST"])
def mark_all_read(request):
    """
    Mark all of the user's notifications as read
    """
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    
    # Return JSON response if requested via AJAX, otherwise redirect
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'message': 'All notifications marked as read'
        })
    
    # Redirect back to the previous page for non-AJAX requests
    return redirect(request.META.get('HTTP_REFERER', '/'))

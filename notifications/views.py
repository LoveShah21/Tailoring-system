"""
Notifications App - Views

Handles notification listing and management.
"""

from django.views.generic import View, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Notification

class NotificationListAPI(LoginRequiredMixin, View):
    """
    API to get recent notifications for the user.
    Returns JSON for the notification dropdown.
    """
    
    def get(self, request):
        # specific to customer? or all users?
        # Assuming all users have notifications based on recipient field
        
        unread_count = Notification.objects.filter(
            recipient=request.user, 
            status__in=['QUEUED', 'SENT', 'DELIVERED'] # Assuming these count as unread if no explicit READ status
        ).count()
        
        notifications = Notification.objects.filter(
            recipient=request.user
        ).order_by('-created_at')[:10]
        
        data = []
        for n in notifications:
            data.append({
                'id': n.id,
                'message': n.message_text or n.subject,
                'type': n.notification_type.display_name,
                'created_at': n.created_at.strftime('%b %d, %H:%M'),
                'is_read': n.status == 'READ',
                'link': self._get_link(n)
            })
            
        return JsonResponse({
            'unread_count': unread_count,
            'notifications': data
        })
    
    def _get_link(self, notification):
        # Logic to link to order detail, etc.
        if notification.order:
            # Check user role to determine order link
            if self.request.user.has_role('customer'):
                # Assuming customer dashboard has link or order detail
                return f"/dashboard/" # Simple fallback
            else:
                return f"/orders/{notification.order.id}/"
        return "#"

class MarkNotificationReadAPI(LoginRequiredMixin, View):
    """Mark a notification as read."""
    
    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
        notification.status = 'READ'
        notification.read_at = timezone.now()
        notification.save()
        return JsonResponse({'status': 'success'})

class MarkAllReadAPI(LoginRequiredMixin, View):
    """Mark all notifications as read."""
    
    def post(self, request):
        Notification.objects.filter(
            recipient=request.user,
            status__in=['QUEUED', 'SENT', 'DELIVERED'] # 'FAILED' ?
        ).update(status='READ', read_at=timezone.now())
        return JsonResponse({'status': 'success'})

from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from core.models import Notification

class NotificationView(APIView):
    def serialize_notification(self, notification):
        return {
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'severity': notification.severity,
            'severity_display': notification.get_severity_display(),
            'source': notification.source,
            'source_display': notification.get_source_display(),
            'acknowledged': notification.acknowledged,
            'acknowledged_by': notification.acknowledged_by,
            'acknowledged_at': notification.acknowledged_at,
            'created_at': notification.created_at,
            'updated_at': notification.updated_at,
            'hash_key': notification.hash_key
        }

    def get(self, request, notification_id=None):
        if notification_id:
            # Get single notification
            notification = get_object_or_404(Notification, id=notification_id)
            return Response(self.serialize_notification(notification))
        else:
            # List all notifications with optional filters
            notifications = Notification.objects.all()

            # Apply filters
            if request.query_params.get('unacknowledged'):
                notifications = notifications.filter(acknowledged=False)
            if request.query_params.get('severity'):
                notifications = notifications.filter(severity=request.query_params['severity'])
            if request.query_params.get('source'):
                notifications = notifications.filter(source=request.query_params['source'])

            # Convert to list of detailed dicts
            return Response([
                self.serialize_notification(n) for n in notifications
            ])

    def post(self, request, notification_id):
        # Handle acknowledgment
        notification = get_object_or_404(Notification, id=notification_id)
        
        if request.path.endswith('/acknowledge/'):
            if notification.acknowledged:
                return Response({
                    'error': 'Notification is already acknowledged'
                }, status=status.HTTP_400_BAD_REQUEST)

            notification.acknowledged = True
            notification.acknowledged_by = request.user.username
            notification.acknowledged_at = timezone.now()
            notification.save()

            return Response({
                'message': 'Notification acknowledged successfully'
            })

        return Response({
            'error': 'Invalid operation'
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, notification_id):
        notification = get_object_or_404(Notification, id=notification_id)
        notification.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

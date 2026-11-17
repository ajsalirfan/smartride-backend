# ============================
# 🔔 NOTIFICATION VIEWS
# ============================

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from Users.models import Notification
from Users.serializers import NotificationSerializer


# ------------------------------------------------------------
# GET: All notifications for logged-in user
# ------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_list(request):
    user = request.user
    notifications = Notification.objects.filter(user=user).order_by('-created_at')
    serializer = NotificationSerializer(notifications, many=True)
    return Response({"notifications": serializer.data})


# ------------------------------------------------------------
# GET: Unread notifications only
# ------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unread_notifications(request):
    user = request.user
    unread = Notification.objects.filter(user=user, is_read=False).order_by('-created_at')
    serializer = NotificationSerializer(unread, many=True)
    return Response({"unread": serializer.data})


# ------------------------------------------------------------
# POST: Mark **single notification** as read
# Body: { "notification_id": 5 }
# ------------------------------------------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_read(request):
    notif_id = request.data.get("notification_id")
    user = request.user

    if not notif_id:
        return Response({"error": "notification_id is required"}, status=400)

    try:
        notif = Notification.objects.get(id=notif_id, user=user)
    except Notification.DoesNotExist:
        return Response({"error": "Notification not found"}, status=404)

    notif.mark_as_read()
    return Response({"message": "Notification marked as read"})


# ------------------------------------------------------------
# POST: Mark ALL notifications as read
# ------------------------------------------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_notifications_read(request):
    user = request.user
    Notification.objects.filter(user=user, is_read=False).update(
        is_read=True,
        read_at=None
    )
    return Response({"message": "All notifications marked as read"})


# ------------------------------------------------------------
# GET: Single notification detail
# ------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_detail(request, notification_id):
    user = request.user
    try:
        notif = Notification.objects.get(id=notification_id, user=user)
    except Notification.DoesNotExist:
        return Response({"error": "Notification not found"}, status=404)

    serializer = NotificationSerializer(notif)
    return Response(serializer.data)


# ------------------------------------------------------------
# GET: Unread count (for header bell icon)
# ------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unread_count(request):
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return Response({"unread_count": count})


# ------------------------------------------------------------
# POST: Notification settings (Custom feature)
# Example: enable/disable types
# ------------------------------------------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def notification_settings(request):
    """
    Optional future feature.
    For now, just return OK to avoid frontend errors.
    """
    return Response({"message": "Notification settings saved"})

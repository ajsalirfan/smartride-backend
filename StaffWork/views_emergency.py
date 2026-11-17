# StaffWork/views_emergency.py
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from Users.models import EmergencyAlert, Notification
from .serializers import EmergencyAlertSerializer, EmergencyAlertUpdateSerializer
from .models import StaffMember


# ======================================================
# 📌 STAFF: LIST ALL EMERGENCIES
# ======================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def staff_emergency_list(request):
    # Ensure staff
    try:
        StaffMember.objects.get(user=request.user)
    except StaffMember.DoesNotExist:
        return Response({"error": "Not a staff account"}, status=403)

    alerts = EmergencyAlert.objects.all().order_by("-created_at")
    serializer = EmergencyAlertSerializer(alerts, many=True)

    active = [e for e in serializer.data if not e["is_resolved"]]
    history = [e for e in serializer.data if e["is_resolved"]]

    return Response({
        "status": True,
        "emergencies": serializer.data,
        "active": active,
        "history": history
    })


# ======================================================
# 📌 STAFF: GET SINGLE EMERGENCY DETAILS
# ======================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def staff_emergency_detail(request, alert_id):
    try:
        alert = EmergencyAlert.objects.get(id=alert_id)
    except EmergencyAlert.DoesNotExist:
        return Response({"error": "Alert not found"}, status=404)

    return Response({
        "status": True,
        "emergency": EmergencyAlertSerializer(alert).data
    })


# ======================================================
# 📌 STAFF: UPDATE / RESOLVE EMERGENCY
# ======================================================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def staff_update_emergency(request, alert_id):

    # Validate staff
    try:
        staff = StaffMember.objects.get(user=request.user)
    except StaffMember.DoesNotExist:
        return Response({"error": "Not a staff account"}, status=403)

    # Fetch alert
    try:
        alert = EmergencyAlert.objects.get(id=alert_id)
    except EmergencyAlert.DoesNotExist:
        return Response({"error": "Alert not found"}, status=404)

    data = request.data.copy()

    # Staff text response → admin_response
    if "response" in data:
        data["admin_response"] = data["response"]
        alert.response_sent_at = timezone.now()

    # Optional staff notes
    if "notes" in data:
        data["resolution_notes"] = data["notes"]

    # Resolve logic
    if str(data.get("is_resolved")).lower() in ["true", "1", "yes"]:
        data["is_resolved"] = True
        alert.resolved_at = timezone.now()
        alert.resolved_by = request.user

    serializer = EmergencyAlertUpdateSerializer(alert, data=data, partial=True)

    if not serializer.is_valid():
        return Response({"status": False, "errors": serializer.errors}, status=400)

    serializer.save()

    # ======================================================
    # 🔔 SEND NOTIFICATION TO USER (DYNAMIC MESSAGE)
    # ======================================================
    Notification.objects.create(
        user=alert.user,
        notification_type="emergency_alert",
        title="Emergency Update",
        message=f"Staff Response: {alert.admin_response}",
        data={"alert_id": alert.id},
        is_sent=True
    )

    return Response({
        "status": True,
        "message": "Emergency updated successfully",
        "updated": EmergencyAlertSerializer(alert).data
    })

# ======================================================
# 🚴‍♂ SMART RIDE ADMIN PANEL — POLISHED VISUAL EDITION
# ======================================================

from django.contrib import admin, messages
from django.utils.html import format_html
from django.shortcuts import redirect
from django.urls import path
from django import forms
from django.template.response import TemplateResponse

# 📧 Email Utilities
from Users.email_utils import (
    send_verification_approved_email,
    send_verification_rejected_email,
    send_welcome_email,
    send_staff_credentials_email,
    send_complaint_reply_email,
    send_feedback_reply_email,
    send_emergency_resolution_email,
)

# 🧩 Models
from Users.models import (
    CustomUser, DocumentUpload, Ride, Payment, Notification,
    LoginHistory, EmergencyAlert, Complaint, Vehicle, Feedback, Wallet
)
# from StaffWork.models import StaffMember, MaintenanceTask
from StaffWork.models import StaffMember, Task



# ======================================================
# 📄 DOCUMENT VERIFICATION
# ======================================================

@admin.register(DocumentUpload)
class DocumentUploadAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'license_front_preview',
        'license_back_preview',
        'id_proof_preview',
        'colored_status',
        'uploaded_at'
    )
    list_filter = ('is_verified',)
    actions = ['approve_documents', 'reject_documents']

    def colored_status(self, obj):
        """Show color badges for verification status."""
        if obj.is_verified:
            return format_html('<b style="color:#22c55e;">🟢 Approved</b>')
        else:
            return format_html('<b style="color:#f43f5e;">🔴 Pending/Rejected</b>')
    colored_status.short_description = "Verification Status"

    def license_front_preview(self, obj):
        return format_html('<a href="{}" target="_blank">📄 View</a>', obj.license_front.url) if obj.license_front else "—"
    def license_back_preview(self, obj):
        return format_html('<a href="{}" target="_blank">📄 View</a>', obj.license_back.url) if obj.license_back else "—"
    def id_proof_preview(self, obj):
        return format_html('<a href="{}" target="_blank">📄 View</a>', obj.id_proof.url) if obj.id_proof else "—"

    def approve_documents(self, request, queryset):
        """Approve docs + email user"""
        for doc in queryset:
            user = doc.user
            doc.is_verified = True
            doc.save()
            user.is_verified = True
            user.verification_status = 'approved'
            user.save()
            send_verification_approved_email(user)
        messages.success(request, f"✅ {queryset.count()} user(s) approved & notified.")

    def reject_documents(self, request, queryset):
        """Reject docs + email user"""
        for doc in queryset:
            user = doc.user
            doc.is_verified = False
            doc.save()
            user.is_verified = False
            user.verification_status = 'rejected'
            user.save()
            send_verification_rejected_email(user, "Document verification failed.")
        messages.error(request, f"❌ {queryset.count()} user(s) rejected & notified.")


# ======================================================
# 💬 COMPLAINT MANAGEMENT
# ======================================================

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('user', 'colored_status', 'title', 'created_at')
    search_fields = ('user__username', 'title')
    fields = ('user', 'complaint_type', 'title', 'description', 'status', 'admin_reply', 'created_at')
    readonly_fields = ('created_at',)

    def colored_status(self, obj):
        color_map = {
            'open': '#facc15',
            'in_progress': '#3b82f6',
            'resolved': '#22c55e',
            'closed': '#6b7280'
        }
        color = color_map.get(obj.status.lower(), '#f97316')
        emoji = '🟢' if obj.status == 'resolved' else '🟡' if obj.status == 'open' else '🔵'
        return format_html(f'<b style="color:{color};">{emoji} {obj.status.title()}</b>')
    colored_status.short_description = "Status"

    def save_model(self, request, obj, form, change):
        if 'admin_reply' in form.changed_data and obj.admin_reply:
            send_complaint_reply_email(obj.user, obj)
            messages.success(request, f"📩 Complaint reply sent to {obj.user.email}")
        super().save_model(request, obj, form, change)


# ======================================================
# 💡 FEEDBACK MANAGEMENT
# ======================================================

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'star_rating', 'created_at')
    readonly_fields = ('created_at',)

    def star_rating(self, obj):
        """Render star rating visually."""
        return format_html('⭐' * obj.rating + f' ({obj.rating}/5)')
    star_rating.short_description = "Rating"

    def save_model(self, request, obj, form, change):
        if 'admin_reply' in form.changed_data and obj.admin_reply:
            send_feedback_reply_email(obj.user, obj)
            messages.success(request, f"💬 Feedback reply sent to {obj.user.email}")
        super().save_model(request, obj, form, change)


# ======================================================
# 🚨 EMERGENCY ALERTS
# ======================================================

@admin.register(EmergencyAlert)
class EmergencyAlertAdmin(admin.ModelAdmin):
    list_display = ('user', 'alert_type_icon', 'colored_status', 'created_at')
    actions = ['mark_as_resolved']

    def alert_type_icon(self, obj):
        icons = {
            'sos': '🆘 SOS',
            'accident': '💥 Accident',
            'breakdown': '🔧 Breakdown',
            'harassment': '🚨 Harassment',
            'medical': '🏥 Medical'
        }
        return icons.get(obj.alert_type, obj.alert_type)
    alert_type_icon.short_description = "Alert Type"

    def colored_status(self, obj):
        if obj.is_resolved:
            return format_html('<b style="color:#22c55e;">🟢 Resolved</b>')
        else:
            return format_html('<b style="color:#ef4444;">🔴 Active</b>')
    colored_status.short_description = "Status"

    def mark_as_resolved(self, request, queryset):
        for alert in queryset:
            alert.is_resolved = True
            alert.save()
            send_emergency_resolution_email(alert.user, alert)
        messages.success(request, f"🚨 {queryset.count()} alert(s) resolved & users notified.")


# ======================================================
# 📜 LOGIN HISTORY (READ ONLY)
# ======================================================

@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'login_time', 'ip_address', 'colored_success')

    def colored_success(self, obj):
        color = '#22c55e' if obj.success else '#ef4444'
        emoji = '✅' if obj.success else '❌'
        return format_html(f'<b style="color:{color};">{emoji}</b>')
    colored_success.short_description = "Login Success"

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False


# ======================================================
# 👥 USERS (ONLY NORMAL USERS)
# ======================================================

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'colored_type', 'colored_verified')
    search_fields = ('username', 'email')
    list_filter = ('user_type', 'is_verified')

    def colored_verified(self, obj):
        color = '#22c55e' if obj.is_verified else '#f43f5e'
        emoji = '🟢' if obj.is_verified else '🔴'
        return format_html(f'<b style="color:{color};">{emoji} {"Verified" if obj.is_verified else "Not Verified"}</b>')
    colored_verified.short_description = "Verification"

    def colored_type(self, obj):
        color_map = {'admin': '#8b5cf6', 'staff': '#3b82f6', 'user': '#10b981'}
        return format_html(f'<b style="color:{color_map.get(obj.user_type, "#374151")};">{obj.user_type.title()}</b>')
    colored_type.short_description = "User Type"

    def get_queryset(self, request):
        """Show only normal users."""
        qs = super().get_queryset(request)
        return qs.filter(user_type='user')

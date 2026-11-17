# ======================================================
# 🚴‍♂ SMART RIDE ADMIN PANEL — FINAL POLISHED PRODUCTION EDITION
# ======================================================

from django.contrib import admin, messages
from django.utils.html import format_html
from django.shortcuts import redirect
from django.urls import path
from django import forms
from django.template.response import TemplateResponse
from django.contrib.admin import AdminSite
from django.contrib.auth.models import Group, User
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.db.models import Q

# 📧 Email Utilities
from Users.email_utils import (
    send_verification_approved_email,
    send_verification_rejected_email,
    send_welcome_email,
    send_staff_credentials_email,
    send_complaint_reply_email,
    send_feedback_reply_email,
    send_emergency_resolution_email,
    send_task_assigned_email,
)

# 🧩 Models
from Users.models import (
    CustomUser, DocumentUpload, Ride, Payment, Notification,
    LoginHistory, EmergencyAlert, Complaint, Vehicle, Feedback, Wallet
)
from StaffWork.models import StaffMember, Task


# ======================================================
# 🧑‍💼 STAFF REGISTRATION FORM
# ======================================================
class RegisterStaffForm(forms.Form):
    name = forms.CharField(max_length=100, label="Full Name")
    email = forms.EmailField(label="Email ID")
    password = forms.CharField(max_length=50, label="Temporary Password")
    role = forms.CharField(max_length=100, required=False, label="Role")


class AdminNotificationForm(forms.Form):
    target_group = forms.ChoiceField(
        choices=[
            ('users', 'All Users'),
            ('staff', 'All Staff'),
            ('both', 'Users + Staff'),
        ],
        label="Send To"
    )
    title = forms.CharField(max_length=255, label="Title")
    message = forms.CharField(widget=forms.Textarea, label="Message")
    notification_type = forms.ChoiceField(
        choices=[
            ('general', 'General'),
            ('ride', 'Ride'),
            ('payment', 'Payment'),
            ('safety', 'Safety'),
            ('system', 'System'),
        ],
        label="Type"
    )


# ======================================================
# 🧠 CUSTOM SMART RIDE ADMIN SITE
# ======================================================
class SmartRideAdminSite(AdminSite):
    site_header = "🚴‍♂ SmartRide Administration"
    site_title = "SmartRide Admin"
    index_title = "Welcome, ajsal_admin 👋"
    enable_nav_sidebar = False

    def get_app_list(self, request, app_label=None):
        """Organized dashboard layout with clear sections (Django 5.2+ compatible)."""
        app_list = super().get_app_list(request)
        admin_section = {'name': '🧑‍💼 Admin Section', 'models': []}
        verification_section = {'name': '📂 Verification & Documents', 'models': []}
        users_section = {'name': '👤 Users & Operations', 'models': []}

        for app in app_list:
            for model in app['models']:
                name = model['object_name']

                # Admin section models
                if name in ['StaffMember', 'Task', 'Vehicle', 'Notification']:
                    if name == 'Task':
                        model['name'] = '🧾 Tasks'
                    elif name == 'Vehicle':
                        model['name'] = '🚗 Vehicles'
                    elif name == 'StaffMember':
                        model['name'] = '👷 Staff Members'
                    elif name == 'Notification':
                        model['name'] = '🔔 Notifications'

                    admin_section['models'].append(model)

                # Verification
                elif name == 'DocumentUpload':
                    model['name'] = '📄 Document Uploads'
                    verification_section['models'].append(model)

                # Users section
                elif name in [
                    'CustomUser', 'Ride', 'Payment', 'Wallet',
                    'Complaint', 'Feedback', 'EmergencyAlert', 'LoginHistory'
                ]:
                    emoji_map = {
                        'CustomUser': '👥 Users',
                        'Ride': '🛵 Rides',
                        'Payment': '💳 Payments',
                        'Wallet': '💰 Wallets',
                        'Complaint': '📢 Complaints',
                        'Feedback': '💬 Feedbacks',
                        'EmergencyAlert': '🚨 Emergency Alerts',
                        'LoginHistory': '🕓 Login Histories',
                    }
                    model['name'] = emoji_map.get(name, name)
                    users_section['models'].append(model)

        # ➕ Register Staff shortcut
        admin_section['models'].insert(0, {
            'name': '➕ Register Staff',
            'admin_url': '/smartride-admin/register-staff/',
            'object_name': 'RegisterStaff',
            'perms': {'add': True, 'view': True, 'change': True, 'delete': True},
        })

        # # 🔔 Manual Notification shortcut
        # admin_section['models'].insert(1, {
        #     'name': '🔔 Send Notification',
        #     'admin_url': '/smartride-admin/send-notification/',
        #     'object_name': 'SendNotification',
        #     'perms': {'add': True, 'view': True, 'change': True, 'delete': True},
        # })

        return [admin_section, verification_section, users_section]

    # ============================
    # 🔗 CUSTOM ADMIN URLs
    # ============================
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("register-staff/", self.admin_view(self.register_staff_view), name="register-staff"),
            # path("send-notification/", self.admin_view(self.send_notification_view), name="send-admin-notification"),
        ]
        return custom_urls + urls

    # ======================================================
    # 👷 REGISTER STAFF VIEW
    # ======================================================
    def register_staff_view(self, request):
        if request.method == "POST":
            form = RegisterStaffForm(request.POST)
            if form.is_valid():
                name = form.cleaned_data['name']
                email = form.cleaned_data['email']
                password = form.cleaned_data['password']
                role = form.cleaned_data['role'] or "Field Agent"

                base_username = email.split('@')[0]
                username = base_username
                count = 1
                while CustomUser.objects.filter(username=username).exists():
                    username = f"{base_username}{count}"
                    count += 1

                user = CustomUser.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=name,
                    user_type='staff',
                    is_staff=True,
                    is_verified=True,
                    verification_status='approved',
                )

                StaffMember.objects.create(
                    user=user,
                    role=role,
                    employee_id=f"STF{user.id:04d}"
                )

                send_welcome_email(user)
                send_staff_credentials_email(user, password)

                messages.success(request, f"👷 Staff '{name}' registered & credentials sent!")
                return redirect("/smartride-admin/StaffWork/staffmember/")

        else:
            form = RegisterStaffForm()

        context = {
            **self.each_context(request),
            "form": form,
            "title": "Register New Staff | SmartRide Admin",
        }
        return TemplateResponse(request, "admin/admin_register_staff.html", context)

    # ======================================================
    # 🔔 SIMPLIFIED NOTIFICATION VIEW
    # ======================================================
    def send_notification_view(self, request):
        if request.method == "POST":
            form = AdminNotificationForm(request.POST)
            if form.is_valid():
                group = form.cleaned_data['target_group']
                title = form.cleaned_data['title']
                message_text = form.cleaned_data['message']
                noti_type = form.cleaned_data['notification_type']

                # Select users based on group
                if group == "users":
                    users = CustomUser.objects.filter(user_type="user", is_active=True)
                elif group == "staff":
                    users = CustomUser.objects.filter(user_type="staff", is_active=True)
                else:  # both
                    users = CustomUser.objects.filter(is_active=True)

                # Create notifications
                for user in users:
                    Notification.objects.create(
                        user=user,
                        title=title,
                        message=message_text,
                        notification_type=noti_type,
                        is_sent=True,
                        data={}
                    )

                messages.success(request, f"🔔 Notification sent to {users.count()} users!")
                return redirect("/smartride-admin/")
        else:
            form = AdminNotificationForm()

        return TemplateResponse(request, "admin/base_site.html", {
            **self.each_context(request),
            "title": "Send Notification",
            "content": mark_safe(f"""
                <div style='padding:20px; max-width:600px;'>
                    <h2>🔔 Send Notification</h2>
                    <form method='post'>
                        <input type='hidden' name='csrfmiddlewaretoken' value='{request.COOKIES.get("csrftoken", "")}'>
                        {form.as_p()}
                        <button type='submit' class='button default'>📨 Send Notification</button>
                    </form>
                </div>
            """),
        })


# ======================================================
# 🧩 SMART RIDE ADMIN SITE INSTANCE
# ======================================================
smartride_admin_site = SmartRideAdminSite(name="smartride_admin")


# ======================================================
# 📦 MODEL ADMIN REGISTRATION (FINAL POLISHED)
# ======================================================

# ======================================================
# 🔔 NOTIFICATION ADMIN - SIMPLIFIED
# ======================================================
@admin.register(Notification, site=smartride_admin_site)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_target', 'title', 'notification_type', 'is_read', 'is_sent', 'created_at')
    list_filter = ('notification_type', 'is_read', 'is_sent', 'created_at')
    search_fields = ('title', 'message', 'user__username', 'staff_member__employee_id')
    readonly_fields = ('created_at', 'read_at')

    # Hide data field
    fields = (
        'user',
        'staff_member',
        'notification_type',
        'title',
        'message',
        'is_read',
        'is_sent',
    )

    def save_model(self, request, obj, form, change):
        """
        Fix: Send notification correctly whether:
        - only user is set
        - only staff_member is set
        - both are set
        """
        super().save_model(request, obj, form, change)

        # For USER notifications
        if obj.user and not obj.staff_member:
            obj.is_sent = True
            obj.save()

        # For STAFF notifications
        if obj.staff_member and not obj.user:
            obj.is_sent = True
            obj.save()

        # If BOTH are selected → send both individually
        if obj.user and obj.staff_member:
            # create staff copy
            Notification.objects.create(
                staff_member=obj.staff_member,
                notification_type=obj.notification_type,
                title=obj.title,
                message=obj.message,
                is_sent=True,
            )
            # mark original as user notification
            obj.is_sent = True
            obj.save()

    def get_target(self, obj):
        if obj.user:
            return f"User: {obj.user.username}"
        if obj.staff_member:
            return f"Staff: {obj.staff_member.employee_id}"
        return "Unknown"
    get_target.short_description = "Target"

@admin.register(StaffMember, site=smartride_admin_site)
class StaffMemberAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'user', 'role', 'is_on_duty', 'current_status')
    search_fields = ('employee_id', 'user__username', 'user__email')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(user__user_type='staff')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    # Add the missing 'obj' parameter here
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(Task, site=smartride_admin_site)
class TaskAdmin(admin.ModelAdmin):
    """
    SmartRide Admin — Task Management
    Includes:
    • Vehicle preview
    • Email on task assign
    • Staff notification
    • Change detection
    """

    list_display = ('task_id', 'title', 'priority', 'status', 'vehicle_photo', 'vehicle')
    list_filter = ('priority', 'status', 'task_type')
    search_fields = ('task_id', 'title', 'assigned_to__user__username')

    fields = (
        'task_id', 'title', 'description', 'task_type', 'priority',
        'status', 'vehicle', 'assigned_to', 'due_date'
    )
    readonly_fields = ('task_id',)

    # -------------------------------
    # VEHICLE IMAGE PREVIEW
    # -------------------------------
    def vehicle_photo(self, obj):
        if obj.vehicle and obj.vehicle.photo:
            return format_html(
                '<img src="{}" style="width:60px; height:45px; border-radius:6px; object-fit:cover;" />',
                obj.vehicle.photo.url
            )
        return format_html('<span style="color:#888;">No Image</span>')

    vehicle_photo.short_description = "Photo"

    # -------------------------------
    # SAVE MODEL → SEND EMAIL + NOTIFICATION
    # -------------------------------
    def save_model(self, request, obj, form, change):
        is_new = not change
        previous_status = None

        if change:
            try:
                previous_status = Task.objects.get(pk=obj.pk).status
            except Task.DoesNotExist:
                previous_status = None

        super().save_model(request, obj, form, change)

        staff_user = obj.assigned_to.user  # The staff account

        # ==========================================================
        # 1️⃣ NEW TASK CREATED → SEND NOTIFICATION + EMAIL
        # ==========================================================
        if is_new:
            send_task_assigned_email(obj)

            Notification.objects.create(
                user=staff_user,
                notification_type="system",
                title="New Task Assigned",
                message=f"You have been assigned a new task: {obj.title}",
                data={"task_id": obj.task_id},
                is_sent=True
            )

            messages.success(request, "📩 New Task → Email + Notification sent")
            return

        # ==========================================================
        # 2️⃣ STATUS UPDATED → TASK ASSIGNED (from any other state)
        # ==========================================================
        if previous_status != "assigned" and obj.status == "assigned":
            send_task_assigned_email(obj)

            Notification.objects.create(
                user=staff_user,
                notification_type="system",
                title="Task Assigned",
                message=f"Task assigned: {obj.title}",
                data={"task_id": obj.task_id},
                is_sent=True
            )

            messages.success(request, "📨 Task Assigned → Email + Notification sent")

        # Logging
        print(f"🔔 Task Updated → {obj.task_id} | Status: {obj.status}")

    # -------------------------------
    # FOREIGN KEY DEBUGGING / HANDLER
    # Ensures vehicles appear in dropdown 
    # even during errors or missing data.
    # -------------------------------
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "vehicle":
            model = db_field.remote_field.model
            print(f"DEBUG: Vehicle model = {model}")
            print(f"DEBUG: Total vehicles = {model.objects.count()}")
            kwargs["queryset"] = model.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    
@admin.register(Vehicle, site=smartride_admin_site)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        'vehicle_id',
        'vehicle_type',
        'status',
        'battery_display',
        'photo_preview',
    )
    list_filter = ('vehicle_type', 'status')
    search_fields = ('vehicle_id', 'vehicle_type', 'current_zone')
    readonly_fields = ('photo_preview',)

    def photo_preview(self, obj):
        if obj.photo and hasattr(obj.photo, 'url'):
            return format_html(
                '<img src="{}" style="width:80px; height:60px; border-radius:8px; object-fit:cover;" />',
                obj.photo.url
            )
        return format_html('<span style="color:#999;">No Photo</span>')
    photo_preview.short_description = "Preview"

    def battery_display(self, obj):
        level = obj.battery_level
        color = "#4CAF50" if level >= 60 else "#FFC107" if level >= 30 else "#F44336"
        return format_html(
            '<div style="width:70px; border-radius:6px; background-color:#ddd;">'
            '<div style="width:{}%; background-color:{}; padding:2px 0; border-radius:6px;">'
            '<span style="font-size:12px; color:#fff;">{}%</span>'
            '</div></div>',
            level, color, level
        )
    battery_display.short_description = "Battery"
@admin.register(DocumentUpload, site=smartride_admin_site)
class DocumentUploadAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'aadhaar_preview',
        'license_preview',
        'is_verified',
        'verified_by',
        'verified_at',
        'uploaded_at'
    )
    list_filter = ('is_verified',)
    readonly_fields = (
        'user', 'aadhaar_card', 'driving_license', 'uploaded_at',
        'verified_by', 'verified_at', 'rejection_reason',
    )
    actions = ['approve_documents', 'reject_documents']

    # ------------------------------
    # File Previews
    # ------------------------------
    def aadhaar_preview(self, obj):
        return format_html('<a href="{}" target="_blank">📄 View Aadhaar</a>', obj.aadhaar_card.url) if obj.aadhaar_card else "—"

    def license_preview(self, obj):
        return format_html('<a href="{}" target="_blank">📄 View License</a>', obj.driving_license.url) if obj.driving_license else "—"

    aadhaar_preview.short_description = "Aadhaar Card"
    license_preview.short_description = "Driving License"

    # ------------------------------
    # APPROVE DOCUMENTS
    # ------------------------------
    def approve_documents(self, request, queryset):
        for doc in queryset:
            # Update document status
            doc.is_verified = True
            doc.verified_by = request.user
            doc.verified_at = timezone.now()
            doc.rejection_reason = ""
            doc.save()

            # Update user status
            user = doc.user
            user.is_verified = True
            user.verification_status = 'approved'
            user.save()

            # Send email
            send_verification_approved_email(user)

            # ➕ Send in-app notification
            Notification.objects.create(
                user=user,
                notification_type='system',
                title="Documents Approved",
                message="Your verification documents have been approved successfully.",
                data={"verification_status": "approved"},
                is_sent=True
            )

        messages.success(
            request,
            f"✅ {queryset.count()} user(s) approved and notified!"
        )

    # ------------------------------
    # REJECT DOCUMENTS
    # ------------------------------
    def reject_documents(self, request, queryset):
        for doc in queryset:
            rejection_reason = "Documents not clear or invalid"

            doc.is_verified = False
            doc.verified_by = request.user
            doc.verified_at = timezone.now()
            doc.rejection_reason = rejection_reason
            doc.save()

            user = doc.user
            user.is_verified = False
            user.verification_status = 'rejected'
            user.save()

            # Send email
            send_verification_rejected_email(user, rejection_reason)

            # ➕ Send in-app notification
            Notification.objects.create(
                user=user,
                notification_type='system',
                title="Documents Rejected",
                message="Your submitted documents were rejected. Please upload clearer copies.",
                data={
                    "verification_status": "rejected",
                    "reason": rejection_reason
                },
                is_sent=True
            )

        messages.error(
            request,
            f"❌ {queryset.count()} user(s) rejected & notified!"
        )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(CustomUser, site=smartride_admin_site)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'user_type', 'is_verified', 'verification_status')
    list_filter = ('user_type', 'is_verified', 'verification_status')
    search_fields = ('username', 'email', 'phone_number')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(user_type='customer')

    # 🔒 View-only except DELETE
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True   # ✅ DELETE ENABLED


@admin.register(Complaint, site=smartride_admin_site)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'title', 'complaint_type', 'status',
        'photo_preview', 'created_at'
    )
    search_fields = ('user__username', 'title', 'complaint_type')
    list_filter = ('status', 'complaint_type')
    readonly_fields = (
        'user', 'complaint_type', 'title', 'description',
        'photo', 'photo_preview', 'created_at'
    )

    # ------------------------------
    # 📸 Show Image Preview in Admin
    # ------------------------------
    def photo_preview(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" style="width:120px; border-radius:8px;" />',
                obj.photo.url
            )
        return "No Photo"
    photo_preview.short_description = "Photo Preview"

    # ------------------------------
    # 🚫 No Manual Add
    # ------------------------------
    def has_add_permission(self, request):
        return False

    # ------------------------------
    # 💬 Save Model (Admin Reply Logic)
    # ------------------------------
    def save_model(self, request, obj, form, change):

        # Check if admin_reply changed
        reply_added = (
            change and
            'admin_reply' in form.changed_data and
            obj.admin_reply.strip() != ""
        )

        super().save_model(request, obj, form, change)

        # If reply updated → send email + notification
        if reply_added:

            # 1️⃣ Send email
            send_complaint_reply_email(obj.user, obj)

            # 2️⃣ Send in-app notification
            Notification.objects.create(
                user=obj.user,
                notification_type='safety',
                title='Complaint Update',
                message=f"Admin replied to your complaint: {obj.title}",
                data={
                    'complaint_id': obj.id,
                    'reply': obj.admin_reply
                },
                is_sent=True
            )

            # 3️⃣ Success message in admin
            messages.success(
                request,
                f"📩 Reply sent & notification delivered to {obj.user.username}!"
            )
            
@admin.register(EmergencyAlert, site=smartride_admin_site)
class EmergencyAlertAdmin(admin.ModelAdmin):
    list_display = (
        'colored_user',
        'colored_alert_type',
        'location_name',
        'status_badge',
        'created_at'
    )
    list_filter = ('alert_type', 'is_resolved', 'created_at')
    search_fields = ('user__username', 'message', 'location_name')

    readonly_fields = (
        'user', 'ride', 'alert_type', 'message',
        'location_lat', 'location_lng', 'location_name',
        'contacts_notified', 'created_at',
        'response_sent_at', 'resolved_at'
    )

    # ----------------------------------------------------
    # UI FORMATTING
    # ----------------------------------------------------
    def colored_user(self, obj):
        return f"👤 {obj.user.username}"
    colored_user.short_description = "User"

    def colored_alert_type(self, obj):
        colors = {
            "accident": "red",
            "harassment": "orange",
            "vehicle_breakdown": "blue",
            "medical": "green",
            "theft": "purple",
            "other": "gray",
        }
        color = colors.get(obj.alert_type, "black")
        return format_html(f"<b style='color:{color}'>{obj.alert_type}</b>")
    colored_alert_type.short_description = "Type"

    def status_badge(self, obj):
        return format_html(
            "<span style='color:{};font-weight:bold;'>{}</span>".format(
                "green" if obj.is_resolved else "red",
                "Resolved ✔" if obj.is_resolved else "Pending ⚠️"
            )
        )
    status_badge.short_description = "Status"

    def has_add_permission(self, request):
        return False

    # ----------------------------------------------------
    # SAVE MODEL — CLEAN SIMPLIFIED VERSION
    # ----------------------------------------------------
    def save_model(self, request, obj, form, change):
        """When admin writes a reply, mark resolved + notify user."""

        # Check if admin entered a reply
        reply_added = (
            change and
            'admin_response' in form.changed_data and
            obj.admin_response.strip() != ""
        )

        # Save normally first
        super().save_model(request, obj, form, change)

        if reply_added:
            # Mark emergency resolved
            obj.is_resolved = True
            obj.resolved_at = timezone.now()
            obj.response_sent_at = timezone.now()
            obj.resolved_by = request.user
            obj.save()

            # Send in-app notification with EXACT reply
            Notification.objects.create(
                user=obj.user,
                notification_type='emergency_alert',
                title="Emergency Update",
                message=obj.admin_response,        # 👈 USER SEES ADMIN MESSAGE ONLY
                data={"alert_id": obj.id},
                is_sent=True
            )

            messages.success(
                request,
                f"📨 Reply sent to {obj.user.username}! Emergency marked resolved."
            )
        

@admin.register(LoginHistory, site=smartride_admin_site)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'login_time', 'ip_address', 'success')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True   # ✅ MUST BE TRUE

# @admin.register(Payment, site=smartride_admin_site)
# class PaymentAdmin(admin.ModelAdmin):
#     list_display = ('transaction_id', 'user', 'ride', 'amount', 'status')
#     def has_add_permission(self, request): return False
#     def has_change_permission(self, request, obj=None): return False

@admin.register(Ride, site=smartride_admin_site)
class RideAdmin(admin.ModelAdmin):
    list_display = ('ride_id', 'user', 'vehicle', 'status', 'cost')
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False

@admin.register(Wallet, site=smartride_admin_site)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance')
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False

# ======================================================
# 🚫 UNREGISTER DEFAULT MODELS
# ======================================================
try:
    smartride_admin_site.unregister(Group)
    smartride_admin_site.unregister(User)
except admin.sites.NotRegistered:
    pass
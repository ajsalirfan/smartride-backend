# Admin/services.py
import logging
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

class StaffEmailService:
    """Class-based email service for staff operations"""
    
    @staticmethod
    def send_welcome_email(staff_data, temp_password, staff_profile):
        """Send welcome email to new staff member"""
        try:
            subject = "🚀 Welcome to SmartRide - Staff Account Created"
            
            message = f"""
Dear {staff_data.get('first_name', 'Team Member')},

🎉 WELCOME TO SMART RIDE STAFF TEAM!

Your staff account has been successfully created. Here are your login credentials:

🔐 ACCOUNT CREDENTIALS:
• Username: {staff_data['username']}
• Email: {staff_data['email']}
• Temporary Password: {temp_password}
• Staff ID: {staff_profile.employee_id}
• Role: {staff_data.get('role', 'Staff Member')}

📱 GETTING STARTED:
1. Login URL: {getattr(settings, 'STAFF_LOGIN_URL', 'http://localhost:3000/staff/login')}
2. Change your password after first login
3. Complete your profile setup
4. Check assigned tasks in your dashboard

🔧 STAFF FEATURES:
• Task Management System
• Real-time Notifications  
• Vehicle Status Updates
• Emergency Response Tools
• Performance Analytics

🛡️ SECURITY NOTES:
• Change your password immediately after first login
• Never share your credentials
• Log out after each session

📞 SUPPORT:
• Email: staff-support@smartride.com
• Phone: +1-555-STAFF-SUPPORT

We're excited to have you on board!

Best regards,
Smart Ride Operations Team
            """.strip()

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[staff_data['email']],
                fail_silently=False,
            )
            
            logging.info(f"Welcome email sent to {staff_data['email']}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to send welcome email: {e}")
            return False

    @staticmethod
    def send_task_assignment_email(task, staff_member):
        """Send task assignment email to staff"""
        try:
            subject = f"📋 New Task Assigned - {task.title}"
            
            message = f"""
Hello {staff_member.user.get_full_name() or staff_member.user.username},

📋 NEW TASK ASSIGNMENT

You have been assigned a new task:

TASK DETAILS:
• Task ID: {task.task_id}
• Title: {task.title}
• Type: {task.get_task_type_display()}
• Priority: {task.get_priority_display()}
• Due Date: {task.due_date.strftime('%Y-%m-%d %H:%M') if task.due_date else 'ASAP'}
• Location: {task.location_name or 'Not specified'}

DESCRIPTION:
{task.description}

🚀 ACTION REQUIRED:
1. Review task details in your dashboard
2. Update task status as you progress
3. Mark as completed when finished

Thank you for your commitment!

Smart Ride Operations Team
            """.strip()

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[staff_member.user.email],
                fail_silently=True,
            )
            
            logging.info(f"Task assignment email sent to {staff_member.user.email}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to send task assignment email: {e}")
            return False
# users/email_utils.py - COMPLETE EMAIL NOTIFICATION SYSTEM
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail, get_connection
import sys, traceback
# ==================== EMAIL NOTIFICATION FUNCTIONS ====================

def send_welcome_email(user):
    """Send welcome email after registration"""
    subject = f"🎉 Welcome to SmartRide, {user.username}!"
    
    message = f"""
Hello {user.username},

Welcome to SmartRide! We're excited to have you join our community of eco-friendly riders.

Your account has been successfully created.

GET STARTED:
1. Complete your profile verification by uploading documents
2. Add payment method to your wallet
3. Explore nearby vehicles
4. Take your first ride and earn bonus points!

Download our app: https://smartride.com/download
Need help? Contact support: {settings.SMART_RIDE_CONFIG['SUPPORT_EMAIL']}

Happy Riding!
The SmartRide Team

---
SmartRide - Sustainable Urban Mobility
{settings.SMART_RIDE_CONFIG['SUPPORT_PHONE']}
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send welcome email: {e}")
        return False

def send_document_upload_confirmation_email(user):
    """Send email to user after document upload"""
    subject = f"📄 Documents Uploaded Successfully - SmartRide Verification"
    
    message = f"""
Dear {user.get_full_name() or user.username},

Thank you for submitting your verification documents. We have received your documents and our team will review them shortly.

DOCUMENTS RECEIVED:
✓ Driving License (Front & Back)
✓ ID Proof (Aadhaar/PAN)

WHAT'S NEXT:
• Our verification team will review your documents
• Verification typically takes 24-48 hours
• You'll receive an email once verification is complete
• You can start riding immediately after approval

VERIFICATION STATUS: Pending Review

If you have any questions about the verification process, please contact our support team at {settings.SMART_RIDE_CONFIG['SUPPORT_EMAIL']} or call {settings.SMART_RIDE_CONFIG['SUPPORT_PHONE']}.

Thank you for choosing SmartRide!

Best regards,
SmartRide Verification Team
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send document upload confirmation email: {e}")
        return False

def send_verification_approved_email(user):
    """Send email when user verification is approved"""
    subject = f"✅ Verification Approved - You're Ready to Ride! - SmartRide"
    
    message = f"""
Congratulations {user.get_full_name() or user.username}!

Your SmartRide account has been successfully verified and approved.

🎉 YOUR ACCOUNT IS NOW ACTIVE!

You can now:
• Book rides immediately
• Access all vehicles in your area  
• Earn loyalty points on every ride
• Enjoy our premium features

GET STARTED:
1. Open the SmartRide app
2. Find nearby vehicles on the map
3. Scan QR code to start your ride
4. Enjoy eco-friendly transportation!

Your safety is our priority. Remember to:
• Always wear a helmet
• Follow traffic rules
• Park in designated areas
• Charge responsibly

Need help with your first ride? Contact us:
Email: {settings.SMART_RIDE_CONFIG['SUPPORT_EMAIL']}
Phone: {settings.SMART_RIDE_CONFIG['SUPPORT_PHONE']}

Welcome to the SmartRide community!

Happy Riding! 🚀

Best regards,
SmartRide Team
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send verification approved email: {e}")
        return False

def send_verification_rejected_email(user, rejection_reason):
    """Send email when user verification is rejected"""
    subject = f"❌ Verification Requires Attention - SmartRide"
    
    # Common rejection reasons and solutions
    common_solutions = {
        "blurry_documents": "Please upload clear, high-quality photos of your documents without any glare or blur.",
        "expired_documents": "Please ensure all documents are valid and not expired.",
        "name_mismatch": "Please ensure the name on all documents matches exactly.",
        "invalid_document_numbers": "Please double-check your document numbers for accuracy.",
        "poor_quality_selfie": "Please upload a clear selfie where your face and the document are both visible.",
        "missing_documents": "Please ensure you have uploaded all required documents.",
        "document_cutoff": "Please ensure the entire document is visible in the photo without any edges cut off.",
        "illegible_information": "Please ensure all text on the documents is clear and readable."
    }
    
    # Get specific solution based on rejection reason
    solution = common_solutions.get(rejection_reason.lower().replace(" ", "_"), 
        "Please review the uploaded documents and ensure they meet our verification standards.")
    
    message = f"""
Dear {user.get_full_name() or user.username},

We've reviewed your verification documents, but we need some additional information to complete your verification.

REASON FOR REJECTION:
{rejection_reason}

REQUIRED ACTION:
{solution}

HOW TO RESUBMIT:
1. Log in to your SmartRide account
2. Go to Profile → Verification
3. Upload new, clear documents
4. Ensure all information matches your official documents
5. Click 'Submit for Verification'

DOCUMENT REQUIREMENTS:
• Clear, high-quality photos (no blur or glare)
• All four corners of documents visible
• Valid, non-expired documents
• Name must match exactly across all documents

COMMON ISSUES TO AVOID:
• Blurry or unclear photos
• Expired documents
• Name mismatches between documents
• Incorrect document numbers
• Documents with cut-off edges

If you need assistance with document upload, our support team is here to help:
📧 Email: {settings.SMART_RIDE_CONFIG['SUPPORT_EMAIL']}
📞 Phone: {settings.SMART_RIDE_CONFIG['SUPPORT_PHONE']}
🕒 Support Hours: 24/7

We're looking forward to having you on board! Once your documents are approved, you'll be ready to start riding immediately.

Best regards,
SmartRide Verification Team

---
Note: This is an automated message. Please do not reply to this email.
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send verification rejected email: {e}")
        return False

def send_welcome_back_email(user, total_logins, last_login=None):
    """Send welcome back email after login"""
    days_info = ""
    if last_login:
        days_since = (timezone.now() - last_login).days
        if days_since > 30:
            days_info = f" We've missed you! It's been {days_since} days since your last visit."
        elif days_since > 7:
            days_info = f" Welcome back after {days_since} days."
    
    subject = f"👋 Welcome back to SmartRide, {user.username}!"
    
    message = f"""
Hello {user.username},{days_info}

Good to see you back on SmartRide!

Ready to ride?
• Find nearby vehicles
• Check your wallet balance  
• Update your favorite locations

Need assistance? Contact us:
Email: {settings.SMART_RIDE_CONFIG['SUPPORT_EMAIL']}
Phone: {settings.SMART_RIDE_CONFIG['SUPPORT_PHONE']}

Stay safe and enjoy your ride!

Best regards,
SmartRide Team
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send welcome back email: {e}")
        return False

def send_ride_started_email(user, ride, vehicle):
    """Send email when ride starts"""
    subject = f"🚀 Your SmartRide has Started! - Ride #{ride.ride_id}"
    
    message = f"""
Hi {user.get_full_name() or user.username},

Your SmartRide has started! Here are your ride details:

RIDE STARTED:
• Ride ID: {ride.ride_id}
• Vehicle: {vehicle.vehicle_id} - {vehicle.vehicle_type}
• Start Time: {ride.start_time.strftime('%Y-%m-%d %H:%M:%S')}
• Start Location: {ride.start_location_name}
• Battery Level: {vehicle.battery_level}%

RIDE SAFETY REMINDERS:
• Always wear a helmet
• Follow traffic rules and speed limits
• Be aware of your surroundings
• Park in designated areas only

RIDE CHARGES:
• Base Fare: ₹10
• Per Minute: ₹2
• Total cost will be calculated after ride completion

NEED HELP DURING RIDE?
• Use the emergency button in the app for immediate assistance
• Contact support: {settings.SMART_RIDE_CONFIG['SUPPORT_PHONE']}
• Emergency contacts will be notified if needed

Enjoy your ride and stay safe!

Best regards,
SmartRide Team

---
Ride safely and responsibly.
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send ride started email: {e}")
        return False

def send_ride_completed_email(user, ride):
    """Send email when ride completes"""
    subject = f"✅ Ride Completed Successfully - Ride #{ride.ride_id}"
    
    message = f"""
Hi {user.get_full_name() or user.username},

Your SmartRide has been completed successfully! Here's your ride summary:

RIDE COMPLETED:
• Ride ID: {ride.ride_id}
• Duration: {int(ride.duration or 0)} minutes
• Distance: {ride.distance or 0} km
• Total Cost: ₹{ride.cost or 0}
• Carbon Saved: {ride.carbon_saved or 0} kg CO2

PAYMENT DETAILS:
• Amount: ₹{ride.cost or 0}
• Payment Method: {ride.payment_method or 'Pending'}
• Payment Status: {ride.payment_status}

LOYALTY POINTS EARNED:
• Base Points: +10 points
• Distance Bonus: +{int((ride.distance or 0) * 2)} points
• Total Earned: +{int(10 + ((ride.distance or 0) * 2))} points

Thank you for choosing eco-friendly transportation!

YOUR NEXT RIDE:
• Find nearby vehicles in the app
• Share your experience with friends
• Earn more loyalty points

Need help or have questions?
Email: {settings.SMART_RIDE_CONFIG['SUPPORT_EMAIL']}
Phone: {settings.SMART_RIDE_CONFIG['SUPPORT_PHONE']}

See you on your next ride! 🚀

Best regards,
SmartRide Team
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send ride completed email: {e}")
        return False

def send_payment_success_email(user, payment, payment_type):
    """Send email for successful payment"""
    if payment_type == 'wallet_topup':
        subject = f"💰 Wallet Top-up Successful - ₹{payment.amount}"
        payment_description = f"Wallet top-up of ₹{payment.amount}"
    else:
        subject = f"✅ Payment Successful - ₹{payment.amount}"
        payment_description = f"Ride payment of ₹{payment.amount}"
    
    message = f"""
Hi {user.get_full_name() or user.username},

Your payment was processed successfully!

PAYMENT CONFIRMED:
• Amount: ₹{payment.amount}
• Transaction ID: {payment.transaction_id}
• Payment Method: {payment.payment_method}
• Date: {payment.payment_completed_at or timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
• Description: {payment_description}

CURRENT WALLET BALANCE: ₹{user.wallet.balance}

Thank you for your payment. Your account has been updated accordingly.

SECURITY NOTE:
If you didn't authorize this payment, please contact our support team immediately.

Need help?
Email: {settings.SMART_RIDE_CONFIG['SUPPORT_EMAIL']}
Phone: {settings.SMART_RIDE_CONFIG['SUPPORT_PHONE']}

Best regards,
SmartRide Payments Team
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send payment success email: {e}")
        return False

def send_emergency_alert_email(user, alert):
    """Send email to user for emergency alert"""
    subject = f"🚨 Emergency Alert Activated - SmartRide Safety"
    
    message = f"""
EMERGENCY ALERT ACTIVATED

Hi {user.get_full_name() or user.username},

Your emergency alert has been activated. Help is on the way!

ALERT DETAILS:
• Alert Type: {alert.alert_type}
• Time: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}
• Location: {alert.location_name or 'Location shared with support'}
• Message: {alert.message or 'No additional message provided'}

IMMEDIATE ACTIONS TAKEN:
✓ Emergency contacts notified
✓ Support team alerted
✓ Your location shared with responders
✓ Assistance dispatched to your location

WHAT TO DO NOW:
1. Stay in a safe location if possible
2. Keep your phone accessible
3. Await contact from support team
4. Follow instructions from responders

SUPPORT CONTACT:
• Emergency: {settings.SMART_RIDE_CONFIG['SUPPORT_PHONE']}
• Support: {settings.SMART_RIDE_CONFIG['SUPPORT_EMAIL']}

Your safety is our top priority. Help is on the way!

Best regards,
SmartRide Safety Team

---
This is an automated emergency alert message.
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send emergency alert email: {e}")
        return False

def send_staff_emergency_alert(alert, is_staff_alert=False):
    """Send email to staff/admin for emergency alerts"""
    if is_staff_alert:
        subject = f"🚨 STAFF EMERGENCY - {alert.user.username} - {alert.alert_type}"
        alert_source = "STAFF MEMBER"
    else:
        subject = f"🚨 USER EMERGENCY - {alert.user.username} - {alert.alert_type}"
        alert_source = "USER"
    
    message = f"""
EMERGENCY ALERT - {alert_source}

URGENT: Emergency alert requires immediate attention!

ALERT DETAILS:
• User: {alert.user.get_full_name() or alert.user.username} ({alert.user.email})
• User Type: {alert.user.user_type}
• Alert Type: {alert.alert_type}
• Time: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}
• Location: {alert.location_name}
• Coordinates: {alert.location_lat}, {alert.location_lng}
• Message: {alert.message or 'No additional message'}

USER CONTACT INFORMATION:
• Phone: {alert.user.phone_number or 'Not provided'}
• Email: {alert.user.email}

IMMEDIATE ACTIONS REQUIRED:
1. Contact user immediately: {alert.user.phone_number or 'Phone not available'}
2. Dispatch nearest available staff
3. Notify emergency services if needed
4. Monitor user location and status
5. Update emergency response team

EMERGENCY CONTACTS (if available):
{get_emergency_contacts_info(alert.user)}

ADMIN PANEL:
http://localhost:8000/admin/Users/emergencyalert/{alert.id}/change/

This is an automated emergency alert from SmartRide Safety System.
"""

    try:
        admin_email = getattr(settings, 'ADMIN_EMAIL', 'admin@smartride.com')
        staff_emails = getattr(settings, 'STAFF_EMAILS', [admin_email])
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=staff_emails,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send staff emergency alert: {e}")
        return False

def send_password_reset_email(user, otp):
    """Send password reset OTP email"""
    subject = f"🔒 Password Reset Request - SmartRide"
    
    message = f"""
Hi {user.get_full_name() or user.username},

We received a request to reset your password for your SmartRide account.

PASSWORD RESET OTP:
{otp}

This OTP is valid for 10 minutes.

To reset your password:
1. Enter this OTP in the password reset page
2. Create a new strong password
3. Confirm your new password

SECURITY TIPS:
• Never share your OTP with anyone
• Create a strong, unique password
• Enable two-factor authentication if available
• Contact support if you didn't request this reset

If you didn't request a password reset, please ignore this email or contact our support team immediately.

Need help?
Email: {settings.SMART_RIDE_CONFIG['SUPPORT_EMAIL']}
Phone: {settings.SMART_RIDE_CONFIG['SUPPORT_PHONE']}

Best regards,
SmartRide Security Team

---
This is an automated security message.
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send password reset email: {e}")
        return False

def send_otp_email(user, otp, purpose):
    """Send OTP email for various purposes"""
    purpose_descriptions = {
        'login': 'login to your account',
        'verification': 'verify your email address',
        'password_reset': 'reset your password'
    }
    
    purpose_description = purpose_descriptions.get(purpose, 'complete your request')
    
    subject = f"🔐 Your SmartRide OTP - {otp}"
    
    message = f"""
Hi {user.get_full_name() or user.username},

Your One-Time Password (OTP) to {purpose_description} is:

{otp}

This OTP is valid for 10 minutes.

SECURITY REMINDER:
• Never share this OTP with anyone
• SmartRide staff will never ask for your OTP
• This OTP is for one-time use only

If you didn't request this OTP, please contact our support team immediately.

Need assistance?
Email: {settings.SMART_RIDE_CONFIG['SUPPORT_EMAIL']}
Phone: {settings.SMART_RIDE_CONFIG['SUPPORT_PHONE']}

Best regards,
SmartRide Security Team

---
This is an automated security message.
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send OTP email: {e}")
        return False

def send_verification_email(user, verification_token):
    """Send email verification email"""
    subject = f"📧 Verify Your Email - SmartRide"
    
    verification_url = f"https://smartride.com/verify-email/{verification_token}"
    
    message = f"""
Hi {user.get_full_name() or user.username},

Welcome to SmartRide! Please verify your email address to complete your account setup.

To verify your email address, click the link below:
{verification_url}

Or copy and paste this link in your browser:
{verification_url}

This verification link will expire in 24 hours.

Why verify your email?
• Secure your account
• Receive important notifications
• Reset your password if needed
• Access all SmartRide features

If you didn't create a SmartRide account, please ignore this email.

Need help?
Email: {settings.SMART_RIDE_CONFIG['SUPPORT_EMAIL']}
Phone: {settings.SMART_RIDE_CONFIG['SUPPORT_PHONE']}

Best regards,
SmartRide Team
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send verification email: {e}")
        return False

# ==================== HELPER FUNCTIONS ====================

def get_emergency_contacts_info(user):
    """Get emergency contacts information for staff alerts"""
    try:
        contacts = user.emergency_contacts.all()
        if not contacts:
            return "No emergency contacts registered"
        
        contacts_info = ""
        for contact in contacts:
            contacts_info += f"• {contact.name}: {contact.phone_number} ({contact.relationship})\n"
        
        return contacts_info
    except Exception as e:
        return f"Error retrieving contacts: {str(e)}"

def send_admin_document_alert(user):
    """Send email to admin about new document submission"""
    subject = f"🆕 New Document Submission - {user.username}"
    
    message = f"""
ADMIN ALERT: New Document Submission

User Details:
• Name: {user.get_full_name() or user.username}
• Email: {user.email}
• User ID: {user.id}
• Submitted At: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}

Documents Submitted:
✓ Driving License Front & Back
✓ ID Proof (Aadhaar/PAN)

ACTION REQUIRED:
Please review the documents in the admin panel and approve/reject the verification.

Admin Panel: http://localhost:8000/admin/Users/customuser/{user.id}/change/

Verification Status: Pending

This is an automated alert from SmartRide Verification System.
"""

    try:
        admin_email = getattr(settings, 'ADMIN_EMAIL', 'admin@smartride.com')
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin_email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send admin alert email: {e}")
        return False

def send_admin_rejection_notification(user, rejection_reason, admin_name):
    """Send email to admin confirming rejection action"""
    subject = f"❌ Verification Rejected - {user.username}"
    
    message = f"""
ADMIN NOTIFICATION: User Verification Rejected

Action: Verification Rejected
Performed By: {admin_name}
Timestamp: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}

User Details:
• Name: {user.get_full_name() or user.username}
• Email: {user.email}
• User ID: {user.id}

Rejection Reason:
{rejection_reason}

Status Updates:
• Verification Status: Rejected
• Account Status: Not Verified
• Can Book Rides: No

Next Steps:
• User has been notified via email
• User can resubmit documents after corrections
• No further action required unless user contacts support

Admin Panel: http://localhost:8000/admin/Users/customuser/{user.id}/change/

This is an automated notification from SmartRide Admin System.
"""

    try:
        admin_email = getattr(settings, 'ADMIN_EMAIL', 'ajsalirfan56@gmail.com')
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin_email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send admin rejection notification: {e}")
        return False
    
def send_accident_alert_email(user, accident_report):
    """Send accident alert email to user and staff"""
    subject = f"🚨 Accident Reported - {user.username} - SmartRide Safety"
    
    message = f"""
ACCIDENT REPORT - URGENT

Hi {user.get_full_name() or user.username},

We have received your accident report and our safety team has been alerted.

ACCIDENT DETAILS:
• Report ID: #{accident_report.id}
• Accident Type: {accident_report.accident_type}
• Severity Level: {accident_report.severity}
• Location: {accident_report.location_name}
• Injuries Reported: {'Yes' if accident_report.injuries_reported else 'No'}
• Emergency Services: {'Called' if accident_report.emergency_services_called else 'Not Called'}

DESCRIPTION:
{accident_report.description}

IMMEDIATE ACTIONS TAKEN:
✓ Safety team notified and responding
✓ Your location shared with emergency responders
✓ Insurance process initiated (if applicable)
✓ Support team assigned to your case

WHAT TO DO NEXT:
1. Ensure your safety first
2. Seek medical attention if needed
3. Contact emergency services if not already done
4. Our support team will contact you shortly

EMERGENCY CONTACTS:
• SmartRide Safety: {settings.SMART_RIDE_CONFIG['SUPPORT_PHONE']}
• Local Emergency: 112 (India Emergency Number)

Your safety is our top priority. Help is on the way!

Best regards,
SmartRide Safety Team
"""

    try:
        # Send to user
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        # Send to admin/staff
        admin_subject = f"🚨 ACCIDENT ALERT - {user.username} - {accident_report.severity.upper()}"
        admin_message = f"""
URGENT: ACCIDENT REPORTED

User: {user.get_full_name() or user.username} ({user.email})
Phone: {user.phone_number or 'Not provided'}
Accident ID: #{accident_report.id}
Severity: {accident_report.severity}
Location: {accident_report.location_name}
Coordinates: {accident_report.location_lat}, {accident_report.location_lng}

DETAILS:
{accident_report.description}

STATUS:
• Injuries: {accident_report.injuries_reported}
• Police Involved: {accident_report.police_report_filed}
• Insurance: {accident_report.insurance_claimed}
• Emergency Services: {accident_report.emergency_services_called}

REQUIRED ACTIONS:
1. Contact user immediately
2. Dispatch nearest staff
3. Coordinate with emergency services if needed
4. Document the incident

Admin Panel: http://localhost:8000/admin/Users/accidentreport/{accident_report.id}/change/
"""
        
        admin_email = getattr(settings, 'ADMIN_EMAIL', 'admin@smartride.com')
        staff_emails = getattr(settings, 'STAFF_EMAILS', [admin_email])
        
        send_mail(
            subject=admin_subject,
            message=admin_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=staff_emails,
            fail_silently=False,
        )
        
        return True
    except Exception as e:
        print(f"Failed to send accident alert email: {e}")
        return False
    
def send_staff_credentials_email(user, plain_password, staff_portal_url="http://localhost:8000/staff/login/"):
    """Send staff login credentials after registration"""
    subject = f"👷 Your SmartRide Staff Account Credentials"
    
    message = f"""
Hello {user.get_full_name() or user.username},

Welcome to the SmartRide Staff Portal! 🎉  
Your staff account has been successfully created.

Here are your login details:

🔑 Login URL: {staff_portal_url}  
👤 Username: {user.email}  
🔐 Temporary Password: {plain_password}

Please log in and change your password immediately after first login.

As a SmartRide staff member, you can:
• Manage maintenance and vehicle updates  
• Handle user reports and emergency alerts  
• Assist users with real-time operations  

For security reasons:
- Do NOT share these credentials with anyone.  
- Reset your password if you suspect unauthorized access.  

If you face any issues logging in, contact the admin team at {settings.SMART_RIDE_CONFIG['SUPPORT_EMAIL']}.

Welcome aboard! 🚴‍♂  
The SmartRide Operations Team
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send staff credentials email: {e}")
        return False

# ======================================================
# 📨 ADMIN REPLY / RESPONSE EMAILS
# ======================================================

def send_complaint_reply_email(user, complaint):
    """Send email when admin replies to a user's complaint."""
    subject = f"📩 Response to Your Complaint - SmartRide"
    message = f"""
Hi {user.get_full_name() or user.username},

Your complaint titled "{complaint.title}" has received a response from our support team.

🧾 Complaint Details:
• Title: {complaint.title}
• Status: {complaint.status}

💬 Admin Reply:
"{complaint.admin_reply}"

If you need further assistance, reply to this email or contact support:
📧 {settings.SMART_RIDE_CONFIG['SUPPORT_EMAIL']}
📞 {settings.SMART_RIDE_CONFIG['SUPPORT_PHONE']}

Thank you for helping us improve SmartRide.

Best regards,
SmartRide Support Team
"""
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
        return True
    except Exception as e:
        print(f"Failed to send complaint reply email: {e}")
        return False


def send_feedback_reply_email(user, feedback):
    """Send email when admin replies to feedback."""
    subject = f"💬 Thanks for Your Feedback - SmartRide"
    message = f"""
Hi {user.get_full_name() or user.username},

Thank you for sharing your feedback with us!

📝 Your Feedback:
"{feedback.message}"

💬 SmartRide Response:
"{feedback.admin_reply}"

Your input helps us improve and provide you with a smoother, safer ride experience.

If you have more suggestions, reply to this email anytime!

Best regards,
SmartRide Team
"""
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
        return True
    except Exception as e:
        print(f"Failed to send feedback reply email: {e}")
        return False


def send_emergency_resolution_email(user, alert):
    """Send email when emergency alert is resolved by admin/staff."""

    subject = (
        f"✔️ Emergency Alert #{alert.id} Resolved — "
        f"User: {user.username} — "
        f"📞 +91 8589833473"
    )

    message = f"""
Hi {user.get_full_name() or user.username},

Your emergency alert has been reviewed and marked as RESOLVED by our SmartRide Safety Team.

===============================
🚨 EMERGENCY ALERT DETAILS
===============================
🆔 Alert ID: {alert.id}
⚠️ Type: {alert.get_alert_type_display()}
📅 Reported At: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}
📍 Location: {alert.location_name or 'Location shared with support'}
🌍 Coordinates: ({alert.location_lat}, {alert.location_lng})

===============================
🛠 ADMIN RESPONSE
===============================
{alert.admin_response or "No additional message provided."}

===============================
📞 NEED MORE HELP?
===============================
You can contact SmartRide Emergency Support anytime:

📧 {settings.SMART_RIDE_CONFIG['SUPPORT_EMAIL']}
📞 {settings.SMART_RIDE_CONFIG['SUPPORT_PHONE']}

OR you may directly reach:
👤 *Your registered number:*  
📞 **+91 8589833473**

If you still feel unsafe or need immediate support, do not hesitate to call emergency services.

Stay safe,  
SmartRide Safety Team
"""

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False
        )
        return True

    except Exception as e:
        print(f"Failed to send emergency resolution email: {e}")
        return False

def send_task_assigned_email(task):
    """
    Enhanced Task Assignment Email Sender 💼
    Sends detailed task info to assigned staff member with better structure and clarity.
    Returns True on success, False on failure.
    """
    try:
        if not task:
            print("⚠️ send_task_assigned_email called with no task.")
            return False

        if not getattr(task, 'assigned_to', None):
            print(f"⚠️ Task {getattr(task, 'task_id', 'UNKNOWN')} has no assigned_to.")
            return False

        # Get staff and user details
        staff_obj = getattr(task.assigned_to, 'user', task.assigned_to)
        recipient = getattr(staff_obj, 'email', None)
        username_display = (
            staff_obj.get_full_name() if callable(getattr(staff_obj, 'get_full_name', None))
            else getattr(staff_obj, 'username', str(staff_obj))
        )

        if not recipient:
            print(f"⚠️ Assigned staff ({username_display}) has no email address. Aborting email.")
            return False

        recipient = recipient.strip()

        # Prepare email details
        subject = f"🛠️ New Task Assigned: {task.title or 'Untitled Task'}"
        due_date_text = task.due_date.strftime('%b %d, %Y') if getattr(task, 'due_date', None) else 'Not specified'
        assigned_by = getattr(task.assigned_by, 'username', 'SmartRide Admin')
        vehicle_info = f"{task.vehicle.vehicle_id} - {task.vehicle.vehicle_type}" if getattr(task, 'vehicle', None) else "N/A"

        message = f"""
Hello {staff_obj.first_name or username_display}, 👋

A new maintenance task has been assigned to you through the SmartRide Admin System.

━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 **TASK DETAILS**
━━━━━━━━━━━━━━━━━━━━━━━━━━━
🆔 Task ID: {task.task_id or 'N/A'}
📋 Title: {task.title or 'N/A'}
🧩 Type: {task.task_type or 'N/A'}
🚗 Vehicle: {vehicle_info}
🎯 Priority: {task.priority or 'N/A'}
📅 Due Date: {due_date_text}
📍 Location: {task.location_name or 'Not provided'}
👷 Assigned By: {assigned_by}
━━━━━━━━━━━━━━━━━━━━━━━━━━━

🕒 **Task Status:** {task.status or 'Pending'}
🗓️ Created At: {task.created_at.strftime('%b %d, %Y, %I:%M %p') if task.created_at else 'Not available'}

💬 **Task Description:**
{task.description or 'No additional details provided.'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 NEXT STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━
1️⃣ Log in to your SmartRide Staff Portal  
2️⃣ Review your assigned task details  
3️⃣ Start the task and update progress once completed  
4️⃣ Mark it as "In Progress" or "Completed" after finishing

👉 Access your dashboard:  
🔗 http://localhost:8000/staff/login/

━━━━━━━━━━━━━━━━━━━━━━━━━━━
This task is important to ensure vehicle reliability and user safety.  
Thank you for keeping SmartRide running smoothly! 🙌

Best Regards,  
🚴 SmartRide Operations Team  
{settings.SMART_RIDE_CONFIG.get('SUPPORT_EMAIL', 'support@smartride.com')}  
{settings.SMART_RIDE_CONFIG.get('SUPPORT_PHONE', '+91-99999-99999')}
"""

        # Send the email
        try:
            connection = get_connection(fail_silently=False)
            result = send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
                connection=connection,
                html_message=message,
            )

            if result:
                print(f"✅ Task assignment email sent successfully to {recipient}")
                return True
            else:
                print(f"❌ send_mail returned {result} while sending to {recipient}.")
                return False
        except Exception:
            print("❌ SMTP/send_mail raised exception:")
            traceback.print_exc(file=sys.stdout)
            return False

    except Exception:
        print("❌ Unexpected error in send_task_assigned_email:")
        traceback.print_exc(file=sys.stdout)
        return False
    

def send_document_upload_confirmation_email(user):
    """Send email to user confirming document upload (DL + ID Proof)."""

    subject = "📄 Documents Uploaded Successfully – SmartRide Verification"

    message = f"""
Hi {user.get_full_name() or user.username},

We’ve successfully received your verification documents.

📑 DOCUMENTS RECEIVED:
• Driving License
• ID Proof (Aadhaar / PAN)

🕒 WHAT HAPPENS NEXT?
• Our verification team will manually review the documents.
• Verification usually takes 24–48 hours.
• You will receive an email notification once your account is approved.
• After approval, you can start booking rides immediately.

🔐 VERIFICATION STATUS: Pending Review

If you uploaded any wrong or unclear files, you can re-upload directly from your profile.

Need help?
📧 {settings.SMART_RIDE_CONFIG['SUPPORT_EMAIL']}
📞 {settings.SMART_RIDE_CONFIG['SUPPORT_PHONE']}

Thanks for choosing SmartRide — your eco-friendly mobility partner! 🚴‍♂️🌱

Warm regards,  
SmartRide Verification Team
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"❌ Failed to send document upload confirmation email: {e}")
        return False

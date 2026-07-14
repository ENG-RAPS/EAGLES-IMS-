# notifications/utils.py
from django.core.mail import send_mail
from django.conf import settings
from .models import Notification
import logging



logger = logging.getLogger(__name__)

def create_notification(user, type, title, message, link=None, send_email=False, send_sms=False, send_whatsapp=False):
    """Create an in-app notification and optionally send via email/sms/whatsapp."""
    # Save in-app notification
    notif = Notification.objects.create(
        user=user,
        notification_type=type,
        title=title,
        message=message,
        link=link,
    )

    # Send email
    if send_email:
        try:
            send_mail(
                subject=title,
                message=f"{message}\n\nView: {link if link else ''}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            notif.sent_via['email'] = True
        except Exception as e:
            logger.error(f"Email failed for {user.email}: {e}")

    # Send SMS – example using Twilio
    if send_sms and user.profile.phone:
        try:
            from twilio.rest import Client
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(
                body=f"{title}: {message}",
                from_=settings.TWILIO_PHONE_NUMBER,
                to=user.profile.phone
            )
            notif.sent_via['sms'] = True
        except Exception as e:
            logger.error(f"SMS failed for {user.profile.phone}: {e}")

    # Send WhatsApp – using Twilio WhatsApp API
    if send_whatsapp and user.profile.phone:
        try:
            from twilio.rest import Client
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(
                body=f"{title}: {message}",
                from_=f'whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}',
                to=f'whatsapp:{user.profile.phone}'
            )
            notif.sent_via['whatsapp'] = True
        except Exception as e:
            logger.error(f"WhatsApp failed for {user.profile.phone}: {e}")

    notif.save(update_fields=['sent_via'])
    return notif
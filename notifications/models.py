from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Notification(models.Model):
    TYPES = (
        ('LOW_STOCK', 'Low Stock'),
        ('PENDING_TXN', 'Pending Transaction'),
        ('PENDING_TRANSFER', 'Pending Transfer'),
        ('PPM_OVERDUE', 'PPM Overdue'),
        ('PPM_UPCOMING', 'Upcoming PPM'),
        ('SYSTEM', 'System Message'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=TYPES)
    title = models.CharField(max_length=100)
    message = models.TextField()
    link = models.URLField(blank=True, null=True)          # optional URL to action page
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    # Optional: channels that were sent (email/sms/whatsapp)
    sent_via = models.JSONField(default=dict, blank=True)  # e.g. {'email': True, 'sms': False}

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"
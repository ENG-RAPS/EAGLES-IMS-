# user/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Branch(models.Model):
    name = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    status = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Department(models.Model):
    name = models.CharField(max_length=100)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='departments')

    def __str__(self):
        return f"{self.name} ({self.branch.name})"



ROLE_CHOICES = (
    ('MAIN_ADMIN', 'Main Admin'),
    ('BRANCH_ADMIN', 'Branch Admin'),
    ('STORE_ADMIN', 'Store Admin'),
    ('STORE_OFFICER', 'Store Officer'),
    ('BIOMED_ADMIN', 'Biomed Admin'),
    ('BIOMED_TECHNICIAN', 'Biomed Technician'),
)
class Profile(models.Model):
    # ... existing fields ...
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STORE_OFFICER')
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    address = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    image = models.ImageField(default='default.png', upload_to='profile_images')
    # New fields:
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.BooleanField(default=True)  # active/inactive
    date_created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.user.username}-Profile'
    
# user/models.py
# ========== NEW: Base Model & Audit Log ==========

class BaseModel(models.Model):
    """
    Abstract base model for all models across apps.
    Provides created_at, updated_at, created_by, branch, is_active.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='%(class)s_created')
    branch = models.ForeignKey('Branch', on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class AuditLog(models.Model):
    """Logs all CREATE, UPDATE, DELETE actions."""
    ACTION_CHOICES = (
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    app_label = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100)
    object_id = models.PositiveIntegerField()
    object_repr = models.CharField(max_length=200)
    changes = models.JSONField(default=dict)
    branch = models.ForeignKey('Branch', on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} {self.action} {self.object_repr} at {self.timestamp}"
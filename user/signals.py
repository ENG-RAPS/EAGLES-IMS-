# user/signals.py - COMPLETE WORKING VERSION

from django.contrib.auth.models import User, Group
from django.db import connection
from django.db.models.signals import post_delete, post_migrate, post_save
from django.dispatch import receiver

from user.middleware import get_current_user
from .models import AuditLog, Profile


# ========== PROFILE AUTO-CREATION SIGNALS ==========
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Auto-create Profile when a new User is created"""
    if created:
        Profile.objects.get_or_create(
            user=instance,
            defaults={
                'role': 'STORE_OFFICER',
                'status': True,
            }
        )


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save Profile when User is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()


# ========== AUDIT LOG FUNCTIONS ==========
def get_audit_user(instance):
    """
    Determine the user responsible for the action.
    Priority:
    1. Current authenticated user from middleware.
    2. created_by field.
    3. requested_by field.
    """
    user = get_current_user()
    if user and user.is_authenticated:
        return user
    return (
        getattr(instance, "created_by", None)
        or getattr(instance, "requested_by", None)
    )


@receiver(post_migrate)
def create_default_groups(sender, **kwargs):
    """Create default user groups after migrations."""
    groups = [
        "Main Admin",
        "Branch Admin",
        "Store Admin",
        "Store Officer",
        "Biomed Admin",
        "Biomed Technician",
    ]
    for group_name in groups:
        Group.objects.get_or_create(name=group_name)


def audit_table_exists():
    """Check whether the AuditLog table exists."""
    return AuditLog._meta.db_table in connection.introspection.table_names()


@receiver(post_save)
def log_create_update(sender, instance, created, **kwargs):
    """Record CREATE and UPDATE actions in the audit log."""
    # Prevent recursion
    if sender is AuditLog:
        return

    # Skip while migrations are creating tables
    if not audit_table_exists():
        return

    # Ignore Django internal models
    if sender._meta.app_label in (
        "admin",
        "auth",
        "contenttypes",
        "sessions",
        "migrations",
    ):
        return

    AuditLog.objects.create(
        user=get_audit_user(instance),
        action="CREATE" if created else "UPDATE",
        app_label=sender._meta.app_label,
        model_name=sender.__name__,
        object_id=instance.pk,
        object_repr=str(instance),
        changes={},
        branch=getattr(instance, "branch", None),
    )


@receiver(post_delete)
def log_delete(sender, instance, **kwargs):
    """Record DELETE actions in the audit log."""
    # Prevent recursion
    if sender is AuditLog:
        return

    # Skip while migrations are creating tables
    if not audit_table_exists():
        return

    # Ignore Django internal models
    if sender._meta.app_label in (
        "admin",
        "auth",
        "contenttypes",
        "sessions",
        "migrations",
    ):
        return

    AuditLog.objects.create(
        user=get_audit_user(instance),
        action="DELETE",
        app_label=sender._meta.app_label,
        model_name=sender.__name__,
        object_id=instance.pk,
        object_repr=str(instance),
        changes={},
        branch=getattr(instance, "branch", None),
    )
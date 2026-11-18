"""
Accounts signals — emit audit events for authentication activities.
"""
import logging

from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.db.models.signals import pre_save, m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import User

logger = logging.getLogger('audit')


@receiver(user_logged_in)
def on_user_logged_in(sender, request, user, **kwargs):
    """Record successful login."""
    from audit.models import AuditLog
    AuditLog.objects.create(
        event_type='LOGIN_SUCCESS',
        user=user,
        username=user.username,
        detail=f"User '{user.username}' logged in.",
    )


@receiver(user_logged_out)
def on_user_logged_out(sender, request, user, **kwargs):
    """Record logout."""
    from audit.models import AuditLog
    if user:
        AuditLog.objects.create(
            event_type='LOGOUT',
            user=user,
            username=user.username,
            detail=f"User '{user.username}' logged out.",
        )


@receiver(user_login_failed)
def on_user_login_failed(sender, credentials, request, **kwargs):
    """Record failed login attempt. Do NOT store the password."""
    from audit.models import AuditLog
    attempted_username = credentials.get('username', '(unknown)')
    AuditLog.objects.create(
        event_type='LOGIN_FAILED',
        username=attempted_username[:150],  # Truncate to field length
        detail='Failed login attempt.',
    )


@receiver(pre_save, sender=User)
def on_user_status_change(sender, instance, **kwargs):
    """Record account activation/deactivation changes."""
    from audit.models import AuditLog
    if instance.pk:
        try:
            old_user = User.objects.get(pk=instance.pk)
            if old_user.is_active != instance.is_active:
                status = 'activated' if instance.is_active else 'deactivated'
                AuditLog.objects.create(
                    event_type='ACCOUNT_STATUS_CHANGE',
                    user=instance,
                    username=instance.username,
                    detail=f"Account '{instance.username}' {status}.",
                )
        except User.DoesNotExist:
            pass


@receiver(m2m_changed, sender=User.groups.through)
def on_user_groups_changed(sender, instance, action, pk_set, **kwargs):
    """Record role assignment changes."""
    from audit.models import AuditLog
    from django.contrib.auth.models import Group

    if action in ('post_add', 'post_remove', 'post_clear'):
        if action == 'post_add' and pk_set:
            group_names = list(Group.objects.filter(pk__in=pk_set).values_list('name', flat=True))
            AuditLog.objects.create(
                event_type='ROLE_ASSIGNED',
                user=instance,
                username=instance.username,
                detail=f"Roles added: {', '.join(group_names)}",
            )
        elif action == 'post_remove' and pk_set:
            group_names = list(Group.objects.filter(pk__in=pk_set).values_list('name', flat=True))
            AuditLog.objects.create(
                event_type='ROLE_REMOVED',
                user=instance,
                username=instance.username,
                detail=f"Roles removed: {', '.join(group_names)}",
            )
        elif action == 'post_clear':
            AuditLog.objects.create(
                event_type='ROLE_REMOVED',
                user=instance,
                username=instance.username,
                detail='All roles cleared.',
            )

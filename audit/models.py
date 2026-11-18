"""
Audit trail models.

Records authentication and account management events.
Privacy and security notes:
- Passwords are NEVER stored.
- Session tokens are NEVER stored.
- Secret keys are NEVER stored.
- Full request bodies are NOT logged.
- Retention policy: For Client Confirmation.
- These records are NOT tamper-proof; production deployment
  should evaluate tamper-evident logging solutions.
"""
from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """
    Simple audit log for authentication and account events.
    """
    EVENT_TYPES = [
        ('LOGIN_SUCCESS', 'Successful Login'),
        ('LOGIN_FAILED', 'Failed Login'),
        ('LOGOUT', 'Logout'),
        ('PASSWORD_CHANGE', 'Password Changed'),
        ('ACCOUNT_STATUS_CHANGE', 'Account Status Changed'),
        ('ROLE_ASSIGNED', 'Role Assigned'),
        ('ROLE_REMOVED', 'Role Removed'),
    ]

    event_type = models.CharField(max_length=30, choices=EVENT_TYPES, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        help_text='The authenticated user involved (if known).',
    )
    username = models.CharField(
        max_length=150,
        blank=True,
        default='',
        help_text='Username attempted or affected (kept even if user is deleted).',
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_actions',
        help_text='The admin/actor who performed the action (if applicable).',
    )
    detail = models.TextField(
        blank=True,
        default='',
        help_text='Human-readable description of the event.',
    )

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Audit Log Entry'
        verbose_name_plural = 'Audit Log Entries'
        indexes = [
            models.Index(fields=['event_type', 'timestamp']),
        ]

    def __str__(self):
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {self.event_type}: {self.username}"

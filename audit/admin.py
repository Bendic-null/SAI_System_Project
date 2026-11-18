"""
Audit admin configuration.
"""
from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Read-only audit log display in Django Admin."""
    list_display = ('timestamp', 'event_type', 'username', 'detail')
    list_filter = ('event_type', 'timestamp')
    search_fields = ('username', 'detail')
    readonly_fields = ('event_type', 'timestamp', 'user', 'username', 'actor', 'detail')
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        # Only superusers may delete audit logs
        return request.user.is_superuser

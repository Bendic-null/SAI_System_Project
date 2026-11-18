"""
Accounts admin configuration.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group

# Unregister defaults and re-register with customizations
admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class NissinUserAdmin(UserAdmin):
    """
    Customized User admin for the Nissin Procurement system.
    Shows role (group) assignments prominently.
    """
    list_display = ('username', 'email', 'first_name', 'last_name',
                    'is_active', 'is_staff', 'get_roles')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email')

    def get_roles(self, obj):
        return ', '.join(obj.groups.values_list('name', flat=True)) or '(none)'
    get_roles.short_description = 'Assigned Roles'


@admin.register(Group)
class NissinGroupAdmin(GroupAdmin):
    """Group admin showing member count."""
    list_display = ('name', 'get_member_count')

    def get_member_count(self, obj):
        return obj.user_set.count()
    get_member_count.short_description = 'Members'

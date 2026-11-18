"""
Management command to set up provisional system roles (groups).

This command is idempotent — safe to run multiple times.
It will NOT remove existing groups or users.
It will NOT grant permissions to groups (permissions are provisional
and await client confirmation).

Usage:
    python manage.py setup_roles
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


PROVISIONAL_ROLES = [
    ('system-administrator', 'System Administrator'),
    ('enduser-maintenance-lead', 'End-user / Maintenance Lead'),
    ('pr-creator', 'PR Creator'),
    ('odm', 'ODM'),
    ('procurement-specialist', 'Procurement Specialist'),
    ('procurement-site-lead', 'Procurement Site Lead'),
    ('laguna-manager', 'Laguna Manager'),
    ('sic-stockroom-gr-creator', 'SIC / Stockroom / GR Creator'),
    ('dct', 'DCT'),
    ('accounting-finance', 'Accounting & Finance'),
]


class Command(BaseCommand):
    help = 'Create provisional system role groups (idempotent).'

    def handle(self, *args, **options):
        created_count = 0
        existing_count = 0

        for slug, display_name in PROVISIONAL_ROLES:
            group, created = Group.objects.get_or_create(name=slug)
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f'  Created group: {slug} ({display_name})'
                ))
            else:
                existing_count += 1
                self.stdout.write(
                    f'  Already exists: {slug} ({display_name})'
                )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Done. Created: {created_count}, Already existed: {existing_count}'
        ))
        self.stdout.write(self.style.WARNING(
            'NOTE: These are provisional role definitions. '
            'Final permissions await client confirmation.'
        ))
        self.stdout.write(self.style.WARNING(
            'NOTE: No permissions have been assigned to these groups. '
            'Use Django Admin to configure permissions when confirmed.'
        ))

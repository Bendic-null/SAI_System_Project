"""
Accounts views — authentication, dashboard, role workspaces, and password management.
"""
import logging
from urllib.parse import urlparse

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST, require_http_methods

from .forms import NissinLoginForm, NissinPasswordChangeForm

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Role definitions — provisional until client confirms final permissions
# ---------------------------------------------------------------------------
ROLE_DEFINITIONS = {
    'system-administrator': {
        'display': 'System Administrator',
        'description': 'Full system administration including user and role management.',
        'phase_status': 'Active — user and role management available via Django Admin.',
    },
    'enduser-maintenance-lead': {
        'display': 'End-user / Maintenance Lead',
        'description': 'Create and track indirect-material requests.',
        'phase_status': 'Future module — request creation not yet implemented.',
    },
    'pr-creator': {
        'display': 'PR Creator',
        'description': 'Create and manage Purchase Requisitions for indirect materials.',
        'phase_status': 'Future module — PR creation not yet implemented.',
    },
    'odm': {
        'display': 'ODM',
        'description': 'Review and approve material requests at the department level.',
        'phase_status': 'Future module — approval workflow not yet implemented.',
    },
    'procurement-specialist': {
        'display': 'Procurement Specialist',
        'description': 'Source suppliers, manage quotations, and process purchase orders.',
        'phase_status': 'Future module — procurement workflow not yet implemented.',
    },
    'procurement-site-lead': {
        'display': 'Procurement Site Lead',
        'description': 'Oversee procurement operations and approve purchase orders.',
        'phase_status': 'Future module — PO approval not yet implemented.',
    },
    'laguna-manager': {
        'display': 'Laguna Manager',
        'description': 'Manage and approve operations for the Laguna site.',
        'phase_status': 'Future module — site management not yet implemented.',
    },
    'sic-stockroom-gr-creator': {
        'display': 'SIC / Stockroom / GR Creator',
        'description': 'Manage receiving, stockroom inventory, and goods receipt creation.',
        'phase_status': 'Future module — inventory and GR not yet implemented.',
    },
    'dct': {
        'display': 'DCT',
        'description': 'Document Control — manage procurement documentation and compliance.',
        'phase_status': 'Future module — document control not yet implemented.',
    },
    'accounting-finance': {
        'display': 'Accounting & Finance',
        'description': 'Invoice processing, payment tracking, and financial reporting.',
        'phase_status': 'Future module — finance workflow not yet implemented.',
    },
}


def _is_safe_redirect(url, request):
    """Validate a redirect URL to prevent open redirects."""
    if not url:
        return False
    return url_has_allowed_host_and_scheme(
        url=url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    )


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------
@csrf_protect
@require_http_methods(["GET", "POST"])
def login_view(request):
    """Handle user login with Django's authentication system."""
    if request.user.is_authenticated:
        return redirect('accounts:home')

    if request.method == 'POST':
        form = NissinLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            logger.info("User '%s' logged in successfully.", user.username)

            # Handle safe redirect
            next_url = request.POST.get('next') or request.GET.get('next', '')
            if next_url and _is_safe_redirect(next_url, request):
                return redirect(next_url)
            return redirect('accounts:home')
        else:
            logger.info("Failed login attempt.")
    else:
        form = NissinLoginForm(request)

    next_url = request.GET.get('next', '')
    return render(request, 'accounts/login.html', {
        'form': form,
        'next': next_url,
    })


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------
@require_POST
@csrf_protect
def logout_view(request):
    """Log out the user via POST with CSRF protection."""
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        logger.info("User '%s' logged out.", username)
    return redirect('accounts:login')


# ---------------------------------------------------------------------------
# Home / Dashboard
# ---------------------------------------------------------------------------
@login_required
def home_view(request):
    """Authenticated home page showing user info and role-based navigation."""
    user = request.user
    user_groups = user.groups.values_list('name', flat=True)

    # Build list of available role workspaces
    available_roles = []
    for slug, info in ROLE_DEFINITIONS.items():
        if slug in user_groups:
            available_roles.append({
                'slug': slug,
                'display': info['display'],
                'description': info['description'],
                'phase_status': info['phase_status'],
            })

    # Check admin access
    is_admin = user.is_superuser or user.is_staff

    context = {
        'user': user,
        'available_roles': available_roles,
        'is_admin': is_admin,
        'has_roles': len(available_roles) > 0,
        'display_name': user.get_full_name() or user.username,
    }
    return render(request, 'accounts/home.html', context)


# ---------------------------------------------------------------------------
# Role Workspace
# ---------------------------------------------------------------------------
@login_required
def role_workspace_view(request, role_slug):
    """Display a role workspace if the user has the matching group."""
    if role_slug not in ROLE_DEFINITIONS:
        return render(request, 'accounts/access_denied.html', {
            'message': 'The requested workspace does not exist.',
        }, status=403)

    user_groups = set(request.user.groups.values_list('name', flat=True))

    if role_slug not in user_groups:
        return render(request, 'accounts/access_denied.html', {
            'message': 'You do not have permission to access this workspace. '
                       'Contact your system administrator if you need access.',
        }, status=403)

    role_info = ROLE_DEFINITIONS[role_slug]
    context = {
        'role_slug': role_slug,
        'role_display': role_info['display'],
        'role_description': role_info['description'],
        'phase_status': role_info['phase_status'],
    }
    return render(request, 'accounts/workspace.html', context)


# ---------------------------------------------------------------------------
# Access Denied
# ---------------------------------------------------------------------------
def access_denied_view(request):
    """Generic access denied page."""
    return render(request, 'accounts/access_denied.html', {
        'message': 'You do not have permission to access this page.',
    }, status=403)


# ---------------------------------------------------------------------------
# Password Change
# ---------------------------------------------------------------------------
@login_required
@csrf_protect
@require_http_methods(["GET", "POST"])
def password_change_view(request):
    """Allow authenticated users to change their password."""
    if request.method == 'POST':
        form = NissinPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Keep the user logged in after password change
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been changed successfully.')
            logger.info("User '%s' changed their password.", user.username)
            return redirect('accounts:home')
    else:
        form = NissinPasswordChangeForm(request.user)

    return render(request, 'accounts/password_change.html', {'form': form})

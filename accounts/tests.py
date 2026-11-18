"""
Automated tests for accounts app: authentication, roles, workspaces, and audit events.
"""
from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse

from audit.models import AuditLog


class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = "StrongPass123!"
        self.user = User.objects.create_user(
            username="active_user",
            password=self.password,
            is_active=True
        )
        self.inactive_user = User.objects.create_user(
            username="inactive_user",
            password=self.password,
            is_active=False
        )

    def test_login_page_loads(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nissin Procurement")

    def test_valid_credentials_authenticate(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'active_user',
            'password': self.password,
        })
        self.assertRedirects(response, reverse('accounts:home'))
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_invalid_credentials_rejected(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'active_user',
            'password': 'WrongPassword999!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username or password")
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_inactive_user_cannot_login(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'inactive_user',
            'password': self.password,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_safe_local_next_redirect(self):
        response = self.client.post(f"{reverse('accounts:login')}?next=/accounts/password-change/", {
            'username': 'active_user',
            'password': self.password,
        })
        self.assertRedirects(response, '/accounts/password-change/')

    def test_unsafe_external_next_redirect_rejected(self):
        response = self.client.post(f"{reverse('accounts:login')}?next=https://malicious-site.example.com", {
            'username': 'active_user',
            'password': self.password,
        })
        # Should fallback safely to home instead of redirecting externally
        self.assertRedirects(response, reverse('accounts:home'))

    def test_logout_requires_post_and_clears_session(self):
        self.client.login(username='active_user', password=self.password)
        # GET should be disallowed
        get_response = self.client.get(reverse('accounts:logout'))
        self.assertEqual(get_response.status_code, 405)

        # POST logs out
        post_response = self.client.post(reverse('accounts:logout'))
        self.assertRedirects(post_response, reverse('accounts:login'))
        self.assertFalse('_auth_user_id' in self.client.session)


class RoleWorkspaceTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = "StrongPass123!"
        self.user_no_role = User.objects.create_user(
            username="norole_user",
            password=self.password
        )
        self.user_pr = User.objects.create_user(
            username="pr_user",
            password=self.password
        )
        self.group_pr = Group.objects.create(name="pr-creator")
        self.group_sec = Group.objects.create(name="procurement-specialist")
        self.user_pr.groups.add(self.group_pr)

    def test_unauthenticated_redirected(self):
        response = self.client.get(reverse('accounts:home'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('accounts:login')))

    def test_user_with_no_role_can_access_home(self):
        self.client.login(username='norole_user', password=self.password)
        response = self.client.get(reverse('accounts:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No Operational Roles Assigned")

    def test_user_can_access_assigned_workspace(self):
        self.client.login(username='pr_user', password=self.password)
        response = self.client.get(reverse('accounts:workspace', args=['pr-creator']))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "PR Creator")

    def test_user_cannot_access_unassigned_workspace(self):
        self.client.login(username='pr_user', password=self.password)
        # Direct URL check to an unassigned role workspace
        response = self.client.get(reverse('accounts:workspace', args=['procurement-specialist']))
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "Access Denied", status_code=403)


class AuditTrailTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = "StrongPass123!"
        self.user = User.objects.create_user(
            username="audit_user",
            password=self.password
        )

    def test_login_and_logout_creates_audit_log(self):
        # Successful login
        self.client.post(reverse('accounts:login'), {
            'username': 'audit_user',
            'password': self.password,
        })
        self.assertTrue(
            AuditLog.objects.filter(event_type='LOGIN_SUCCESS', username='audit_user').exists()
        )

        # Logout
        self.client.post(reverse('accounts:logout'))
        self.assertTrue(
            AuditLog.objects.filter(event_type='LOGOUT', username='audit_user').exists()
        )

    def test_failed_login_creates_audit_log_without_password(self):
        self.client.post(reverse('accounts:login'), {
            'username': 'audit_user',
            'password': 'bad_password_to_never_store',
        })
        failed_log = AuditLog.objects.filter(event_type='LOGIN_FAILED', username='audit_user').first()
        self.assertIsNotNone(failed_log)
        # Verify raw password is not leaked in detail text
        self.assertNotIn('bad_password_to_never_store', failed_log.detail)

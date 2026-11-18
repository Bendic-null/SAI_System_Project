"""
Account forms for authentication and password management.
"""
from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm


class NissinLoginForm(AuthenticationForm):
    """
    Custom login form with styled widgets.
    Uses Django's built-in AuthenticationForm which handles
    credential validation and inactive-user checks.
    """
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Username',
            'autocomplete': 'username',
            'autofocus': True,
            'id': 'id_username',
        }),
        label='Username',
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Password',
            'autocomplete': 'current-password',
            'id': 'id_password',
        }),
        label='Password',
    )

    error_messages = {
        'invalid_login': 'Invalid username or password. Please try again.',
        'inactive': 'This account is inactive. Please contact your system administrator.',
    }


class NissinPasswordChangeForm(PasswordChangeForm):
    """
    Styled password change form using Django's built-in validation.
    """
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Current password',
            'autocomplete': 'current-password',
            'autofocus': True,
        }),
        label='Current password',
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'New password',
            'autocomplete': 'new-password',
        }),
        label='New password',
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Confirm new password',
            'autocomplete': 'new-password',
        }),
        label='Confirm new password',
    )

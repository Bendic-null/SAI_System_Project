"""
URL configuration for Nissin Procurement & Inventory Management System.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('', RedirectView.as_view(url='/accounts/home/', permanent=False)),
]

# Customize admin site
admin.site.site_header = 'Nissin Procurement — Administration'
admin.site.site_title = 'Nissin Procurement Admin'
admin.site.index_title = 'Site Administration'

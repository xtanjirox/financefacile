"""
Mixin classes for core views.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404

from accounts.models import Company


class CompanyMixin(LoginRequiredMixin):
    """
    Mixin to handle company-related functionality for views.
    """
    def get_company(self):
        """Get the company for the current user."""
        if hasattr(self, 'request') and hasattr(self.request.user, 'profile'):
            return self.request.user.profile.company
        return None

    def get_queryset(self):
        """Filter queryset by company if user is authenticated and has a company."""
        queryset = super().get_queryset()
        company = self.get_company()
        if company:
            return queryset.filter(company=company)
        return queryset.none()

    def get_context_data(self, **kwargs):
        """Add company to the template context."""
        context = super().get_context_data(**kwargs)
        context['company'] = self.get_company()
        return context

    def form_valid(self, form):
        """Set the company for the object being created/updated."""
        if hasattr(form, 'instance') and hasattr(form.instance, 'company'):
            company = self.get_company()
            if company and not form.instance.company:
                form.instance.company = company
        return super().form_valid(form)

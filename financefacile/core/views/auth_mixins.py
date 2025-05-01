from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages

class BaseViewMixin(LoginRequiredMixin):
    """
    Base mixin that requires login for all views
    """
    login_url = 'login'
    redirect_field_name = 'next'

class StaffRequiredMixin(UserPassesTestMixin):
    """
    Mixin that requires the user to be staff
    """
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to access this page.")
        return redirect('dashboard')

class ProductPermissionMixin(UserPassesTestMixin):
    """
    Mixin that checks if user has permissions to manage products
    """
    def test_func(self):
        user = self.request.user
        # Allow staff and superusers
        if user.is_staff or user.is_superuser:
            return True
        # Check for specific product permissions
        return (user.has_perm('core.view_product') or 
                user.has_perm('core.add_product') or 
                user.has_perm('core.change_product') or 
                user.has_perm('core.delete_product'))
    
    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to manage products.")
        return redirect('dashboard')

class ExpensePermissionMixin(UserPassesTestMixin):
    """
    Mixin that checks if user has permissions to manage expenses
    """
    def test_func(self):
        user = self.request.user
        # Allow staff and superusers
        if user.is_staff or user.is_superuser:
            return True
        # Check for specific expense permissions
        return (user.has_perm('core.view_expense') or 
                user.has_perm('core.add_expense') or 
                user.has_perm('core.change_expense') or 
                user.has_perm('core.delete_expense'))
    
    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to manage expenses.")
        return redirect('dashboard')

class InvoicePermissionMixin(UserPassesTestMixin):
    """
    Mixin that checks if user has permissions to manage invoices
    """
    def test_func(self):
        user = self.request.user
        # Allow staff and superusers
        if user.is_staff or user.is_superuser:
            return True
        # Check for specific invoice permissions
        return (user.has_perm('core.view_invoice') or 
                user.has_perm('core.add_invoice') or 
                user.has_perm('core.change_invoice') or 
                user.has_perm('core.delete_invoice'))
    
    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to manage invoices.")
        return redirect('dashboard')

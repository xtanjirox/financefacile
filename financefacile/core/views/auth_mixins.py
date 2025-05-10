from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from django.db.models import Q

class BaseViewMixin(LoginRequiredMixin):
    """
    Base mixin that requires login for all views
    """
    login_url = 'auth:login'
    redirect_field_name = 'next'

class StaffRequiredMixin(UserPassesTestMixin):
    """
    Mixin that requires the user to be staff
    """
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to access this page.")
        return redirect('home')

class ProductPermissionMixin(UserPassesTestMixin):
    """
    Mixin that checks if user has permissions to manage products
    """
    def test_func(self):
        user = self.request.user
        # Allow staff and superusers
        if user.is_staff or user.is_superuser:
            return True
            
        # Allow company admins for their company's products
        if hasattr(user, 'profile') and user.profile and user.profile.is_company_admin:
            return True
            
        # Check for specific product permissions based on the view type
        if self.__class__.__name__.endswith('CreateView'):
            return user.has_perm('core.add_product')
        elif self.__class__.__name__.endswith('UpdateView'):
            return user.has_perm('core.change_product')
        elif self.__class__.__name__.endswith('DeleteView'):
            return user.has_perm('core.delete_product')
        else:  # ListView, DetailView, etc.
            return user.has_perm('core.view_product')
    
    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to manage products.")
        return redirect('home')

class ExpensePermissionMixin(UserPassesTestMixin):
    """
    Mixin that checks if user has permissions to manage expenses
    """
    def test_func(self):
        user = self.request.user
        # Allow staff and superusers
        if user.is_staff or user.is_superuser:
            return True
            
        # Allow company admins for their company's expenses
        if hasattr(user, 'profile') and user.profile and user.profile.is_company_admin:
            return True
            
        # Check for specific expense permissions based on the view type
        if self.__class__.__name__.endswith('CreateView'):
            return user.has_perm('core.add_expense')
        elif self.__class__.__name__.endswith('UpdateView'):
            return user.has_perm('core.change_expense')
        elif self.__class__.__name__.endswith('DeleteView'):
            return user.has_perm('core.delete_expense')
        else:  # ListView, DetailView, etc.
            return user.has_perm('core.view_expense')
    
    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to manage expenses.")
        return redirect('home')

class InvoicePermissionMixin(UserPassesTestMixin):
    """
    Mixin that checks if user has permissions to manage invoices
    """
    def test_func(self):
        user = self.request.user
        # Allow staff and superusers
        if user.is_staff or user.is_superuser:
            return True
            
        # Allow company admins for their company's invoices
        if hasattr(user, 'profile') and user.profile and user.profile.is_company_admin:
            return True
            
        # Check for specific invoice permissions based on the view type
        if self.__class__.__name__.endswith('CreateView'):
            return user.has_perm('core.add_invoice')
        elif self.__class__.__name__.endswith('UpdateView'):
            return user.has_perm('core.change_invoice')
        elif self.__class__.__name__.endswith('DeleteView'):
            return user.has_perm('core.delete_invoice')
        else:  # ListView, DetailView, etc.
            return user.has_perm('core.view_invoice')
    
    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to manage invoices.")
        return redirect('home')


class CategoryPermissionMixin(UserPassesTestMixin):
    """
    Mixin that checks if user has permissions to manage categories
    """
    def test_func(self):
        user = self.request.user
        # Allow staff and superusers
        if user.is_staff or user.is_superuser:
            return True
            
        # Allow company admins for their company's categories
        if hasattr(user, 'profile') and user.profile and user.profile.is_company_admin:
            return True
            
        # Check for specific category permissions based on the view type
        if self.__class__.__name__.endswith('CreateView'):
            return user.has_perm('core.add_entrycategory')
        elif self.__class__.__name__.endswith('UpdateView'):
            return user.has_perm('core.change_entrycategory')
        elif self.__class__.__name__.endswith('DeleteView'):
            return user.has_perm('core.delete_entrycategory')
        else:  # ListView, DetailView, etc.
            return user.has_perm('core.view_entrycategory')
    
    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to manage categories.")
        return redirect('home')


class FinanceEntryPermissionMixin(UserPassesTestMixin):
    """
    Mixin that checks if user has permissions to manage finance entries
    """
    def test_func(self):
        user = self.request.user
        # Allow staff and superusers
        if user.is_staff or user.is_superuser:
            return True
            
        # Allow company admins for their company's finance entries
        if hasattr(user, 'profile') and user.profile and user.profile.is_company_admin:
            return True
            
        # Check for specific finance entry permissions based on the view type
        if self.__class__.__name__.endswith('CreateView'):
            return user.has_perm('core.add_financeentry')
        elif self.__class__.__name__.endswith('UpdateView'):
            return user.has_perm('core.change_financeentry')
        elif self.__class__.__name__.endswith('DeleteView'):
            return user.has_perm('core.delete_financeentry')
        else:  # ListView, DetailView, etc.
            return user.has_perm('core.view_financeentry')
    
    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to manage finance entries.")
        return redirect('home')


class CompanyFilterMixin:
    """
    Mixin that filters querysets by company for company admins.
    This ensures company admins only see data related to their company.
    """
    company_field = 'company'  # Default field name for company relationship
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Superusers and staff can see all data
        if user.is_superuser or user.is_staff:
            return queryset
            
        # Company admins and regular users can only see their company's data
        if hasattr(user, 'profile') and user.profile and user.profile.company:
            company = user.profile.company
            filter_kwargs = {self.company_field: company}
            return queryset.filter(**filter_kwargs)
            
        # Users without a company can't see any data
        return queryset.none()

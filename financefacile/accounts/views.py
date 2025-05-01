from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import UpdateView, FormView, DetailView, TemplateView, View, CreateView, ListView
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import PasswordChangeView, LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.db import transaction

from .models import Company, CompanySettings, UserProfile
from .forms import (UserProfileForm, CustomPasswordChangeForm, UserPermissionsForm, 
                   CompanyForm, CompanySettingsForm, UserCompanyForm)

class ProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'accounts/profile.html'
    context_object_name = 'user_profile'
    
    def get_object(self):
        return self.request.user

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = 'accounts/profile_form.html'
    success_url = reverse_lazy('profile')
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Your profile has been updated successfully!')
        return super().form_valid(form)

class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    form_class = CustomPasswordChangeForm
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('profile')
    
    def form_valid(self, form):
        messages.success(self.request, 'Your password has been changed successfully!')
        return super().form_valid(form)

class IsAdminMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

class IsCompanyAdminMixin(UserPassesTestMixin):
    def test_func(self):
        # Check if user is a company admin for their company
        return (self.request.user.is_authenticated and 
                hasattr(self.request.user, 'profile') and 
                self.request.user.profile.company and 
                self.request.user.profile.is_company_admin)

class UserPermissionsView(LoginRequiredMixin, IsAdminMixin, UpdateView):
    model = User
    form_class = UserPermissionsForm
    template_name = 'accounts/user_permissions.html'
    success_url = reverse_lazy('users-list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Permissions for {self.object.username} have been updated successfully!')
        return super().form_valid(form)

class UsersListView(LoginRequiredMixin, IsAdminMixin, TemplateView):
    template_name = 'accounts/users_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = User.objects.all().order_by('username')
        return context

@login_required
def toggle_user_active(request, pk):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('users-list')
    
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, 'You cannot deactivate your own account.')
        return redirect('users-list')
    
    user.is_active = not user.is_active
    user.save()
    
    status = 'activated' if user.is_active else 'deactivated'
    messages.success(request, f'User {user.username} has been {status}.')
    return redirect('users-list')


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('dashboard')
    
    def form_invalid(self, form):
        messages.error(self.request, 'Invalid username or password')
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    next_page = 'login'
    
    def dispatch(self, request, *args, **kwargs):
        messages.info(request, 'You have been logged out.')
        return super().dispatch(request, *args, **kwargs)


# Company Management Views
class CompanyListView(LoginRequiredMixin, IsAdminMixin, ListView):
    """View to list all companies (admin only)"""
    model = Company
    template_name = 'accounts/company_list.html'
    context_object_name = 'companies'
    ordering = ['name']


class CompanyCreateView(LoginRequiredMixin, IsAdminMixin, CreateView):
    """View to create a new company (admin only)"""
    model = Company
    form_class = CompanyForm
    template_name = 'accounts/company_form.html'
    success_url = reverse_lazy('company-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Company created successfully.')
        return super().form_valid(form)


class CompanyUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View to update company information (admin or company admin)"""
    model = Company
    form_class = CompanyForm
    template_name = 'accounts/company_form.html'
    success_url = reverse_lazy('company-list')
    
    def test_func(self):
        company = self.get_object()
        # Allow access if user is superuser/staff or company admin for this company
        return (self.request.user.is_staff or 
                self.request.user.is_superuser or 
                (hasattr(self.request.user, 'profile') and 
                 self.request.user.profile.company == company and 
                 self.request.user.profile.is_company_admin))
    
    def form_valid(self, form):
        messages.success(self.request, 'Company updated successfully.')
        return super().form_valid(form)


class CompanySettingsUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View to update company settings (admin or company admin)"""
    model = CompanySettings
    form_class = CompanySettingsForm
    template_name = 'accounts/company_settings_form.html'
    
    def get_object(self):
        # Get the company settings for the specified company
        company_id = self.kwargs.get('pk')
        return get_object_or_404(CompanySettings, company_id=company_id)
    
    def test_func(self):
        company_settings = self.get_object()
        # Allow access if user is superuser/staff or company admin for this company
        return (self.request.user.is_staff or 
                self.request.user.is_superuser or 
                (hasattr(self.request.user, 'profile') and 
                 self.request.user.profile.company == company_settings.company and 
                 self.request.user.profile.is_company_admin))
    
    def get_success_url(self):
        return reverse_lazy('company-detail', kwargs={'pk': self.object.company.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Company settings updated successfully.')
        return super().form_valid(form)


class CompanyDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """View to see company details and settings"""
    model = Company
    template_name = 'accounts/company_detail.html'
    context_object_name = 'company'
    
    def test_func(self):
        company = self.get_object()
        # Allow access if user is superuser/staff or belongs to this company
        return (self.request.user.is_staff or 
                self.request.user.is_superuser or 
                (hasattr(self.request.user, 'profile') and 
                 self.request.user.profile.company == company))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add company members to context
        context['members'] = UserProfile.objects.filter(company=self.object).select_related('user')
        return context


class CompanyMembersView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """View to manage company members"""
    template_name = 'accounts/company_members.html'
    
    def test_func(self):
        company_id = self.kwargs.get('pk')
        company = get_object_or_404(Company, pk=company_id)
        # Allow access if user is superuser/staff or company admin for this company
        return (self.request.user.is_staff or 
                self.request.user.is_superuser or 
                (hasattr(self.request.user, 'profile') and 
                 self.request.user.profile.company == company and 
                 self.request.user.profile.is_company_admin))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company_id = self.kwargs.get('pk')
        company = get_object_or_404(Company, pk=company_id)
        context['company'] = company
        context['members'] = UserProfile.objects.filter(company=company).select_related('user')
        
        # Add all users to context for the add member form (admin only)
        if self.request.user.is_staff or self.request.user.is_superuser:
            context['all_users'] = User.objects.all().order_by('username')
        
        return context


@login_required
def assign_user_to_company(request, user_id, company_id):
    """Assign a user to a company and optionally make them a company admin"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('company-list')
    
    user = get_object_or_404(User, pk=user_id)
    company = get_object_or_404(Company, pk=company_id)
    is_admin = request.POST.get('is_company_admin', False) == 'on'
    
    # Update the user's profile
    profile = user.profile
    profile.company = company
    profile.is_company_admin = is_admin
    profile.save()
    
    messages.success(request, f'User {user.username} has been assigned to {company.name}.')
    return redirect('company-members', pk=company_id)


@login_required
def remove_user_from_company(request, user_id, company_id):
    """Remove a user from a company"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('company-list')
    
    user = get_object_or_404(User, pk=user_id)
    company = get_object_or_404(Company, pk=company_id)
    
    # Check if user belongs to this company
    if user.profile.company != company:
        messages.error(request, f'User {user.username} is not a member of {company.name}.')
        return redirect('company-members', pk=company_id)
    
    # Remove user from company
    profile = user.profile
    profile.company = None
    profile.is_company_admin = False
    profile.save()
    
    messages.success(request, f'User {user.username} has been removed from {company.name}.')
    return redirect('company-members', pk=company_id)

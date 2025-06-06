from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404, HttpResponse
from django.urls import reverse_lazy, reverse
from django.views.generic import UpdateView, FormView, DetailView, TemplateView, View, CreateView, ListView
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import PasswordChangeView, LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.db import transaction
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.backends import ModelBackend
from accounts.backends import EmailBackend
from utils.email_utils import send_confirmation_email

from .models import Company, CompanySettings, UserProfile
from .forms import (UserProfileForm, CustomPasswordChangeForm, UserPermissionsForm, 
                   CompanyForm, CompanySettingsForm, UserCompanyForm, RegistrationForm, 
                   CompanyUserCreationForm, ResendConfirmationEmailForm)

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
    success_url = reverse_lazy('auth:profile')
    
    def get_object(self):
        return self.request.user
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'instance': self.request.user})
        return kwargs
    
    def form_valid(self, form):
        # No success message
        return super().form_valid(form)
        
    def post(self, request, *args, **kwargs):
        form = self.get_form()
        return self.form_valid(form) if form.is_valid() else self.form_invalid(form)

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


class IsAdminOrCompanyAdminMixin(UserPassesTestMixin):
    """Mixin that allows access to staff, superusers, or company admins for users in their company"""
    def test_func(self):
        # Always allow staff and superusers
        if self.request.user.is_staff or self.request.user.is_superuser:
            return True
            
        # For company admins, check if they're trying to manage a user in their company
        if hasattr(self.request.user, 'profile') and self.request.user.profile.is_company_admin:
            user_to_manage = self.get_object()
            
            # Check if the user being managed has a profile and belongs to the same company
            if hasattr(user_to_manage, 'profile') and hasattr(self.request.user.profile, 'company'):
                return user_to_manage.profile.company == self.request.user.profile.company
                
        return False

class IsCompanyAdminMixin(UserPassesTestMixin):
    def test_func(self):
        # Check if user is a company admin for their company
        return (self.request.user.is_authenticated and 
                hasattr(self.request.user, 'profile') and 
                self.request.user.profile.company and 
                self.request.user.profile.is_company_admin)

class UserPermissionsView(LoginRequiredMixin, IsAdminOrCompanyAdminMixin, UpdateView):
    model = User
    form_class = UserPermissionsForm
    template_name = 'accounts/user_permissions.html'
    
    def get_success_url(self):
        # If user is a company admin, redirect back to company members page
        if (not self.request.user.is_staff and not self.request.user.is_superuser) and \
           hasattr(self.request.user, 'profile') and self.request.user.profile.is_company_admin:
            return reverse('organizations:company-members', kwargs={'pk': self.request.user.profile.company.id})
        # Otherwise, redirect to users list (for staff/superusers)
        return reverse_lazy('users-list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.get_object()
        
        # If the current user is a company admin (not staff/superuser)
        if (not self.request.user.is_staff and not self.request.user.is_superuser) and \
           hasattr(self.request.user, 'profile') and self.request.user.profile.is_company_admin:
            # Limit what company admins can modify
            # Hide staff and superuser options
            if 'is_staff' in form.fields:
                form.fields.pop('is_staff')
            if 'is_superuser' in form.fields:
                form.fields.pop('is_superuser')
            
            # For company admins, show all permissions
            if 'user_permissions' in form.fields:
                # Show all permissions except system ones
                form.fields['user_permissions'].queryset = get_company_admin_permissions()
            
            # Show all groups
            # No filtering needed for groups - company admins can assign any group
        
        return form
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # If user is marked as company admin, ensure they have all necessary permissions
        if hasattr(form.instance, 'profile') and form.instance.profile.is_company_admin:
            ensure_company_admin_permissions(self.object)
            messages.success(self.request, f'{self.object.username} has been granted company admin permissions.')
        
        messages.success(self.request, f'Permissions for {self.object.username} have been updated successfully!')
        return response
    
# Utility functions for permissions management
def get_company_admin_permissions():
    """Get all permissions that a company admin should have"""
    # Exclude admin-specific permissions and auth management
    excluded_apps = ['admin', 'auth', 'contenttypes', 'sessions']
    
    # Return all permissions except those in excluded apps
    return Permission.objects.exclude(content_type__app_label__in=excluded_apps)


def get_default_view_permissions():
    """Get all view permissions that a normal user should have by default"""
    # Exclude admin-specific permissions and auth management
    excluded_apps = ['admin', 'auth', 'contenttypes', 'sessions']
    
    # Get all view permissions except those in excluded apps
    return Permission.objects.filter(
        codename__startswith='view_'
    ).exclude(
        content_type__app_label__in=excluded_apps
    )


def ensure_default_view_permissions(user):
    """Ensure a normal user has view permissions on all models by default"""
    # Get all view permissions
    view_permissions = get_default_view_permissions()
    
    # Add all view permissions to the user
    user.user_permissions.add(*view_permissions)
    
    # Make sure the user is active
    """
    if not user.is_active:
        user.is_active = True
        user.save()
    """

def ensure_company_admin_permissions(user):
    """Ensure a company admin user has all necessary permissions"""
    if hasattr(user, 'profile') and user.profile.is_company_admin:
        # Get all permissions a company admin should have
        admin_permissions = get_company_admin_permissions()
        
        # Add all these permissions to the user
        user.user_permissions.add(*admin_permissions)
        
        # Make sure the user is active
        """
        if not user.is_active:
            user.is_active = True
            user.save()
        """

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


class CustomLoginView(View):
    template_name = 'accounts/login.html'
    
    def get(self, request):
        # If user is already authenticated, redirect to home
        if request.user.is_authenticated:
            return redirect('home')
        return render(request, self.template_name)
    
    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        form_errors = {}
        
        if not username:
            form_errors['username'] = 'Email or username is required'
            return render(request, self.template_name, {
                'form_errors': form_errors,
                'username': username
            })
        
        if not password:
            form_errors['password'] = 'Password is required'
            return render(request, self.template_name, {
                'form_errors': form_errors,
                'username': username
            })
        
        # First check if the user exists and has the correct password
        try:
            # Try to find the user by either username or email
            user = User.objects.filter(
                Q(username=username) | Q(email=username)
            ).first()
            
            if user is None:
                # User doesn't exist
                form_errors['password'] = 'Invalid email/username or password'
                messages.error(request, 'Invalid email/username or password')
                return render(request, self.template_name, {
                    'form_errors': form_errors,
                    'username': username
                })
                
            # Check if the password is correct
            if not user.check_password(password):
                # Incorrect password
                form_errors['password'] = 'Invalid email/username or password'
                messages.error(request, 'Invalid email/username or password')
                return render(request, self.template_name, {
                    'form_errors': form_errors,
                    'username': username
                })
                
            # Check if the user's account is active (email confirmed)
            if not user.is_active:
                messages.error(request, 'Please confirm your email address before logging in. Check your inbox for the confirmation link.')
                return render(request, self.template_name, {
                    'form_errors': {'username': 'Email not confirmed'},
                    'username': username,
                    'show_resend_link': True
                })
            
            # If we get here, the user exists, password is correct, and account is active
            # Specify the backend to use for login
            login(request, user, backend='accounts.backends.EmailBackend')
            
            # Redirect after successful login
            if next_url := request.GET.get('next'):
                return redirect(next_url)
            # Default redirect to home page
            return redirect('home')
                
        except Exception as e:
            # Log the error
            print(f"Error in login process: {e}")
            form_errors['password'] = 'An error occurred during login'
            messages.error(request, 'An error occurred during login')
            return render(request, self.template_name, {
                'form_errors': form_errors,
                'username': username
            })
        
        # Return the form with errors
        return render(request, self.template_name, {
            'form_errors': form_errors,
            'username': username  # Pass back the username to pre-fill the field
        })


class CustomLogoutView(View):
    """Custom logout view that handles both GET and POST requests"""
    
    def get(self, request, *args, **kwargs):
        """Handle GET requests for logout"""
        # Perform the logout
        logout(request)
        # No logout message
        # Redirect to landing page
        return redirect('/landing/')
        
    def post(self, request, *args, **kwargs):
        """Handle POST requests for logout"""
        # Same implementation as GET for consistency
        return self.get(request, *args, **kwargs)


class LandingPageView(TemplateView):
    """View for the landing page"""
    template_name = 'accounts/landing_page.html'
    
    def get(self, request, *args, **kwargs):
        # If user is already authenticated, redirect to home
        if request.user.is_authenticated:
            return redirect('home')
        return super().get(request, *args, **kwargs)


class RegistrationView(FormView):
    """View for user registration with company creation"""
    form_class = RegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('home')
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().get(request, *args, **kwargs)
    
    def generate_unique_username(self, email):
        """Generate a unique username based on the user's email"""
        username = email.split('@')[0]  # Use part before @ as base username
        
        # Check if username exists and append numbers if needed
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        return username
    
    def form_valid(self, form):
        try:
            with transaction.atomic():
                # Generate username from email
                email = form.cleaned_data['email']
                username = self.generate_unique_username(email)
                
                # Create user with generated username but set as inactive until email confirmation
                user = User.objects.create_user(
                    username=username,
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password1'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    is_active=False  # User is inactive until email is confirmed
                )
                
                # Create company for the user
                company = Company.objects.create(
                    name=form.cleaned_data['company_name'],
                    siret_number=form.cleaned_data.get('company_siret', ''),
                    address=form.cleaned_data.get('company_address', ''),
                    phone_number=form.cleaned_data.get('company_phone', '')
                )
                
                # Create or update user profile
                profile, created = UserProfile.objects.get_or_create(user=user)
                profile.company = company
                profile.is_company_admin = True  # Make the user a company admin
                profile.save()
                
                # Send confirmation email
                send_confirmation_email(user)
                
                messages.success(self.request, 'Account created successfully. Please check your email to activate your account.')
                return redirect(self.success_url)
        except Exception as e:
            messages.error(self.request, f'Error creating account: {str(e)}')
            return self.form_invalid(form)


# Company Management Views
class CompanyListView(LoginRequiredMixin, IsAdminMixin, ListView):
    """View to list all companies (admin only)"""
    model = Company
    template_name = 'accounts/company_list_modern.html'
    context_object_name = 'companies'
    ordering = ['name']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add dashboard card data
        context['total_companies'] = Company.objects.count()
        context['total_users'] = UserProfile.objects.filter(company__isnull=False).count()
        context['active_companies'] = Company.objects.filter(userprofile__isnull=False).distinct().count()
        
        return context


class CompanyCreateView(LoginRequiredMixin, IsAdminMixin, CreateView):
    """View to create a new company (admin only)"""
    model = Company
    form_class = CompanyForm
    template_name = 'accounts/company_form_modern.html'
    success_url = reverse_lazy('company-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Company created successfully.')
        return super().form_valid(form)


class CompanyUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View to update company information (admin or company admin)"""
    model = Company
    form_class = CompanyForm
    template_name = 'accounts/company_form_modern.html'
    
    def get_object(self, queryset=None):
        # For staff/superusers, allow editing any company
        if self.request.user.is_staff or self.request.user.is_superuser:
            return super().get_object(queryset)
        
        # For company admins, only allow editing their own company
        if hasattr(self.request.user, 'profile') and self.request.user.profile.company and self.request.user.profile.is_company_admin:
            return self.request.user.profile.company
        
        # If user doesn't have a company or isn't an admin, raise 404
        raise Http404("You don't have permission to edit any company.")
    
    def get_success_url(self):
        # For company admins, redirect back to company detail page
        if (not self.request.user.is_staff and not self.request.user.is_superuser) and \
           hasattr(self.request.user, 'profile') and self.request.user.profile.is_company_admin:
            return reverse('organizations:company-detail', kwargs={'pk': self.object.id})
        # For staff/superusers, redirect to company list
        return reverse_lazy('organizations:company-list')
    
    def test_func(self):
        # Allow access if user is superuser/staff
        if self.request.user.is_staff or self.request.user.is_superuser:
            return True
            
        # For company admins, check if they're trying to edit their own company
        if hasattr(self.request.user, 'profile') and self.request.user.profile.is_company_admin:
            # Get the company ID from the URL
            company_id = self.kwargs.get('pk')
            # Check if it matches the user's company
            return str(self.request.user.profile.company.id) == str(company_id)
            
        return False
    
    def form_valid(self, form):
        messages.success(self.request, 'Company information updated successfully.')
        return super().form_valid(form)


class CompanySettingsUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View to update company settings (admin or company admin)"""
    model = CompanySettings
    form_class = CompanySettingsForm
    template_name = 'accounts/company_settings_form.html'
    
    def get_object(self, queryset=None):
        # For staff/superusers, allow accessing any company settings
        if self.request.user.is_staff or self.request.user.is_superuser:
            company_id = self.kwargs.get('pk')
            return get_object_or_404(CompanySettings, company_id=company_id)
        
        # For company admins, only allow accessing their own company settings
        if hasattr(self.request.user, 'profile') and self.request.user.profile.company:
            return get_object_or_404(CompanySettings, company=self.request.user.profile.company)
        
        # If user doesn't have a company, raise 404
        raise Http404("You don't have access to any company settings.")
    
    def test_func(self):
        company_settings = self.get_object()
        # Allow access if user is superuser/staff or company admin for this company
        return (self.request.user.is_staff or 
                self.request.user.is_superuser or 
                (hasattr(self.request.user, 'profile') and 
                 self.request.user.profile.company == company_settings.company and 
                 self.request.user.profile.is_company_admin))
    
    def get_success_url(self):
        # Redirect back to the same company settings page
        return reverse_lazy('organizations:company-detail', kwargs={'pk': self.object.company.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Company settings updated successfully.')
        return super().form_valid(form)


class CompanyDetailView(LoginRequiredMixin, DetailView):
    """View to see company details and settings"""
    model = Company
    template_name = 'accounts/company_detail_modern.html'
    context_object_name = 'company'
    
    def get_object(self, queryset=None):
        # For staff/superusers, allow viewing any company
        if self.request.user.is_staff or self.request.user.is_superuser:
            return super().get_object(queryset)
        
        # For regular users, always show their own company regardless of URL
        if hasattr(self.request.user, 'profile') and self.request.user.profile.company:
            return self.request.user.profile.company
        
        # If user doesn't have a company, raise 404
        raise Http404("You don't have access to any company.")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add a flag to indicate if the user is viewing their own company
        if hasattr(self.request.user, 'profile') and self.request.user.profile.company:
            context['is_own_company'] = (self.object == self.request.user.profile.company)
        
        # Add company members to the context
        context['members'] = UserProfile.objects.filter(company=self.object).select_related('user')
        
        # Add company settings to the context if they exist
        try:
            context['company_settings'] = self.object.settings
        except CompanySettings.DoesNotExist:
            # Create default settings if they don't exist
            context['company_settings'] = CompanySettings.objects.create(company=self.object)
        
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


class CompanyUserCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """View for company admins to create new user accounts"""
    model = User
    form_class = CompanyUserCreationForm
    template_name = 'accounts/company_user_create.html'
    
    def test_func(self):
        company = self.get_company()
        # Allow access if user is superuser/staff or company admin for this company
        return (self.request.user.is_staff or 
                self.request.user.is_superuser or 
                (hasattr(self.request.user, 'profile') and 
                 self.request.user.profile.company == company and 
                 self.request.user.profile.is_company_admin))
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.get_company()
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['company'] = self.get_company()
        return context
    
    def get_company(self):
        """Helper method to get the company from the URL parameter"""
        company_id = self.kwargs.get('company_id')
        return get_object_or_404(Company, pk=company_id)
    
    def form_valid(self, form):
        # Get the company (already set in the form via get_form_kwargs)
        company = self.get_company()
        
        # Create the user
        response = super().form_valid(form)
        
        # If user is a company admin, ensure they have the right permissions
        if form.cleaned_data.get('is_company_admin', False):
            ensure_company_admin_permissions(form.instance)
            messages.success(self.request, f'User {form.instance.username} has been created as a company admin with full permissions!')
        else:
            messages.success(self.request, f'User {form.instance.username} has been created successfully!')
        
        # Send confirmation email to the new user
        send_confirmation_email(form.instance)
        messages.info(self.request, f'A confirmation email has been sent to {form.instance.email}. The user must confirm their email before they can log in.')
            
        return response
    
    def get_success_url(self):
        company = self.get_company()
        return reverse('organizations:company-members', kwargs={'pk': company.pk})

# Custom error handlers
def handler403(request, exception=None):
    """Custom 403 Forbidden handler that redirects to the dashboard with a message"""
    messages.warning(request, "You don't have permission to access that page. You've been redirected to the dashboard.")
    return redirect('home')


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
    """Remove a user from the database entirely"""
    company = get_object_or_404(Company, pk=company_id)
    
    # Check if user has permission (is staff, superuser, or company admin for this company)
    if not (request.user.is_staff or request.user.is_superuser or 
            (hasattr(request.user, 'profile') and request.user.profile.company == company and 
             request.user.profile.is_company_admin)):
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('organizations:company-members', pk=company_id)
    
    user = get_object_or_404(User, pk=user_id)
    
    # Check if user belongs to this company
    if not hasattr(user, 'profile') or user.profile.company != company:
        messages.error(request, f'User {user.username} is not a member of {company.name}.')
        return redirect('organizations:company-members', pk=company_id)
    
    # Prevent removing yourself
    if user == request.user:
        messages.error(request, 'You cannot remove yourself from the company.')
        return redirect('organizations:company-members', pk=company_id)
    
    # Store username for success message
    username = user.username
    
    # Delete the user from the database entirely
    user.delete()
    
    messages.success(request, f'User {username} has been permanently deleted from the system.')
    return redirect('organizations:company-members', pk=company_id)


@login_required
def delete_company_user(request, user_id, company_id):
    """Delete a user from the system (company admin function)"""
    company = get_object_or_404(Company, pk=company_id)
    
    # Check if user has permission (is staff, superuser, or company admin for this company)
    if not (request.user.is_staff or request.user.is_superuser or 
            (hasattr(request.user, 'profile') and request.user.profile.company == company and 
             request.user.profile.is_company_admin)):
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('organizations:company-members', pk=company_id)
    
    user = get_object_or_404(User, pk=user_id)
    
    # Check if user belongs to this company
    if not hasattr(user, 'profile') or user.profile.company != company:
        messages.error(request, f'User {user.username} is not a member of {company.name}.')
        return redirect('organizations:company-members', pk=company_id)
    
    # Prevent deleting yourself
    if user == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('organizations:company-members', pk=company_id)
    
    # Check if this is a POST request (for confirmation)
    if request.method == 'POST':
        # Store username for success message
        username = user.username
        
        # Delete the user
        user.delete()
        
        messages.success(request, f'User {username} has been deleted from the system.')
        return redirect('organizations:company-members', pk=company_id)
    
    # If it's a GET request, show confirmation page
    return render(request, 'accounts/confirm_delete_user.html', {
        'user_to_delete': user,
        'company': company
    })


def confirm_email(request, uidb64, token):
    """Confirm a user's email address using the token sent in the confirmation email"""
    try:
        # Decode the user id
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    # Check if the user exists and the token is valid
    if user is not None and default_token_generator.check_token(user, token):
        # Activate the user
        user.is_active = True
        user.save()
        
        # Add success message
        messages.success(request, 'Your email has been confirmed! You can now log in to your account.')
        
        # Render the confirmation success page
        return render(request, 'accounts/email_confirmed.html')
    else:
        # Invalid link
        messages.error(request, 'The confirmation link is invalid or has expired.')
        return redirect('home')


class ResendConfirmationEmailView(FormView):
    """View for resending confirmation emails to users who haven't confirmed their email yet"""
    form_class = ResendConfirmationEmailForm
    template_name = 'accounts/resend_confirmation.html'
    success_url = reverse_lazy('login')
    
    def get_initial(self):
        # Pre-fill the email field if provided in the URL
        initial = super().get_initial()
        if email := self.request.GET.get('email'):
            initial['email'] = email
        return initial
    
    def form_valid(self, form):
        email = form.cleaned_data['email']
        user = User.objects.get(email=email)
        
        # Send a new confirmation email
        send_confirmation_email(user)
        
        messages.success(self.request, 'A new confirmation email has been sent. Please check your inbox.')
        return super().form_valid(form)

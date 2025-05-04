from django import forms
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.forms import UserChangeForm, PasswordChangeForm, UserCreationForm
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django import forms
from .models import Company, CompanySettings, UserProfile

class UserProfileForm(forms.ModelForm):
    """Form for updating user profile information"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    avatar = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If the user has a profile, set the initial avatar value
        if self.instance and hasattr(self.instance, 'profile'):
            self.fields['avatar'].initial = self.instance.profile.avatar
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        username = self.cleaned_data.get('username')
        if email and User.objects.filter(email=email).exclude(username=username).exists():
            raise forms.ValidationError('Email address is already in use.')
        return email
        
    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            profile = user.profile
            if 'avatar' in self.cleaned_data:
                profile.avatar = self.cleaned_data['avatar']
                profile.save()
        return user


class CustomPasswordChangeForm(PasswordChangeForm):
    """Custom password change form with better styling"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add any custom styling or attributes to form fields here
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class UserPermissionsForm(forms.ModelForm):
    """Form for managing user permissions"""
    is_company_admin = forms.BooleanField(required=False, label='Company Administrator',
                                         help_text='Designates whether this user can manage company settings')
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    
    user_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text=''
    )
    
    is_staff = forms.BooleanField(required=False, help_text="Designates whether the user can log into the admin site.")
    is_active = forms.BooleanField(required=False, help_text="Designates whether this user should be treated as active.")
    
    class Meta:
        model = User
        fields = ['groups', 'user_permissions', 'is_staff', 'is_active']
        widgets = {
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'is_active': 'Active',
            'is_staff': 'Staff status',
        }
        help_texts = {
            'is_active': 'Designates whether this user should be treated as active. Unselect this instead of deleting accounts.',
            'is_staff': 'Designates whether the user can log into this admin site.',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter permissions to only show relevant ones
        content_types = ContentType.objects.filter(
            model__in=['product', 'expense', 'invoice', 'productcategory', 'expensecategory']
        )
        self.fields['user_permissions'].queryset = Permission.objects.filter(
            content_type__in=content_types
        ).order_by('content_type__app_label', 'content_type__model', 'name')
        
        # Initialize company admin status
        if self.instance and hasattr(self.instance, 'profile'):
            self.fields['is_company_admin'].initial = self.instance.profile.is_company_admin
    
    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit and hasattr(user, 'profile'):
            user.profile.is_company_admin = self.cleaned_data.get('is_company_admin', False)
            user.profile.save()
        return user


class CompanyForm(forms.ModelForm):
    """Form for creating and updating company information"""
    class Meta:
        model = Company
        fields = ('name', 'siret_number', 'address', 'phone_number')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'siret_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }


class CompanyUserCreationForm(UserCreationForm):
    """Form for company admins to create new user accounts"""
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    is_company_admin = forms.BooleanField(required=False, initial=False, 
                                        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
                                        label='Make this user a company administrator')
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'is_company_admin')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to password fields
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email address is already in use.')
        return email
    
    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email')
        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')
        
        if commit:
            user.save()
            
            # Create or update user profile and link to company
            try:
                # Try to get existing profile
                profile, created = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'company': self.company,
                        'is_company_admin': self.cleaned_data.get('is_company_admin', False)
                    }
                )
                
                # If profile already existed, update it
                if not created:
                    profile.company = self.company
                    profile.is_company_admin = self.cleaned_data.get('is_company_admin', False)
                    profile.save()
            except Exception as e:
                # If there's an error creating/updating the profile, log it and re-raise
                print(f"Error creating/updating profile: {e}")
                raise
            
        return user


class CompanySettingsForm(forms.ModelForm):
    """Form for updating company settings"""
    class Meta:
        model = CompanySettings
        fields = ('default_tva_rate', 'stamp_fee')
        widgets = {
            'default_tva_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stamp_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class UserCompanyForm(forms.ModelForm):
    """Form for assigning users to companies and setting company admin status"""
    class Meta:
        model = UserProfile
        fields = ('company', 'is_company_admin')
        widgets = {
            'company': forms.Select(attrs={'class': 'form-control'}),
            'is_company_admin': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class RegistrationForm(UserCreationForm):
    """Form for user registration with company creation"""
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    # Company fields
    company_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    company_siret = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}), 
                                  label='SIRET Number')
    company_address = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    company_phone = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}), 
                                 label='Phone Number')
    
    # Company settings
    default_tva_rate = forms.DecimalField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
                                        initial=19.0, label='Default TVA Rate (%)')
    stamp_fee = forms.DecimalField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
                                 initial=1.0, label='Stamp Fee')
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to password fields
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email address is already in use.')
        return email
    
    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email')
        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')
        
        if commit:
            user.save()
            
            try:
                # Create company
                company = Company.objects.create(
                    name=self.cleaned_data.get('company_name'),
                    siret_number=self.cleaned_data.get('company_siret'),
                    address=self.cleaned_data.get('company_address'),
                    phone_number=self.cleaned_data.get('company_phone')
                )
                
                # Check if company settings already exist for this company
                company_settings, created = CompanySettings.objects.get_or_create(
                    company=company,
                    defaults={
                        'default_tva_rate': self.cleaned_data.get('default_tva_rate') or 19.0,
                        'stamp_fee': self.cleaned_data.get('stamp_fee') or 1.0
                    }
                )
                
                # If settings already existed, update them
                if not created:
                    company_settings.default_tva_rate = self.cleaned_data.get('default_tva_rate') or 19.0
                    company_settings.stamp_fee = self.cleaned_data.get('stamp_fee') or 1.0
                    company_settings.save()
                
                # Create or update user profile and link to company
                user_profile, created = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'company': company,
                        'is_company_admin': True  # Make the user a company admin by default
                    }
                )
                
                # If profile already existed, update it
                if not created:
                    user_profile.company = company
                    user_profile.is_company_admin = True
                    user_profile.save()
            except Exception as e:
                # If any error occurs, the transaction will roll back
                raise forms.ValidationError(f"Error creating company: {str(e)}")
            
        return user

from django import forms
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.forms import UserChangeForm, PasswordChangeForm
from django.contrib.contenttypes.models import ContentType
from .models import Company, CompanySettings, UserProfile

class UserProfileForm(forms.ModelForm):
    """Form for updating user profile information"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        username = self.cleaned_data.get('username')
        if email and User.objects.filter(email=email).exclude(username=username).exists():
            raise forms.ValidationError('Email address is already in use.')
        return email


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
        widget=forms.CheckboxSelectMultiple
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

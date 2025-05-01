from django import forms
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.forms import UserChangeForm, PasswordChangeForm
from django.contrib.contenttypes.models import ContentType

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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter permissions to only show relevant ones
        content_types = ContentType.objects.filter(
            model__in=['product', 'expense', 'invoice', 'productcategory', 'expensecategory']
        )
        self.fields['user_permissions'].queryset = Permission.objects.filter(
            content_type__in=content_types
        ).order_by('content_type__app_label', 'content_type__model', 'name')

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import Company, CompanySettings, UserProfile

# Define an inline admin for UserProfile
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'profile'

# Define a new User admin that includes the UserProfile inline
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_company', 'is_staff')
    list_filter = BaseUserAdmin.list_filter + ('profile__company', 'profile__is_company_admin')
    
    def get_company(self, obj):
        return obj.profile.company if hasattr(obj, 'profile') and obj.profile.company else '-'
    get_company.short_description = 'Company'

# Define the CompanySettings inline for the Company admin
class CompanySettingsInline(admin.StackedInline):
    model = CompanySettings
    can_delete = False
    verbose_name_plural = 'settings'

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'siret_number', 'phone_number', 'created_at')
    search_fields = ('name', 'siret_number')
    inlines = [CompanySettingsInline]

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

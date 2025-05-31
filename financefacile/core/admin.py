from django.contrib import admin
from . import models
from .notifications import Notification

# Base class for all company-specific model admins
class CompanyModelAdmin(admin.ModelAdmin):
    """Base admin class for all models that belong to a company"""
    list_filter = ('company',)
    
    def get_queryset(self, request):
        # If the user is a superuser, show all records
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Otherwise, only show records for the user's company
        if hasattr(request.user, 'profile') and request.user.profile.company:
            return qs.filter(company=request.user.profile.company)
        return qs.none()
    
    def save_model(self, request, obj, form, change):
        # Automatically set the company when creating a new record
        if not change and not obj.company_id and hasattr(request.user, 'profile') and request.user.profile.company:
            obj.company = request.user.profile.company
        # Set the created_by field if it exists and is not already set
        if hasattr(obj, 'created_by') and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Filter foreign key fields to only show options from the user's company
        if db_field.name == 'company' and not request.user.is_superuser:
            if hasattr(request.user, 'profile') and request.user.profile.company:
                kwargs["queryset"] = db_field.related_model.objects.filter(id=request.user.profile.company.id)
        elif db_field.name in ['category', 'entry_category', 'product'] and not request.user.is_superuser:
            if hasattr(request.user, 'profile') and request.user.profile.company:
                kwargs["queryset"] = db_field.related_model.objects.filter(company=request.user.profile.company)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

'''
@admin.register(models.FinanceEntry)
class FinanceEntryAdmin(CompanyModelAdmin):
    list_display = ('entry_label', 'finance_entry_type', 'entry_category', 'entry_value', 'entry_date', 'company')
    list_filter = ('company', 'finance_entry_type', 'entry_category')
    search_fields = ('entry_label',)
'''

@admin.register(models.ExpenseCategory)
class ExpenseCategoryAdmin(CompanyModelAdmin):
    list_display = ('name', 'company')
    search_fields = ('name',)

@admin.register(models.Expense)
class ExpenseAdmin(CompanyModelAdmin):
    list_display = ('category', 'date', 'amount', 'company', 'created_by')
    list_filter = ('company', 'category', 'date')
    search_fields = ('description',)

@admin.register(models.ProductCategory)
class ProductCategoryAdmin(CompanyModelAdmin):
    list_display = ('name', 'parent', 'company')
    list_filter = ('company',)
    search_fields = ('name',)

@admin.register(models.Product)
class ProductAdmin(CompanyModelAdmin):
    list_display = ('name', 'sku', 'category', 'quantity', 'selling_price', 'company')
    list_filter = ('company', 'category')
    search_fields = ('name', 'sku', 'description')

@admin.register(models.InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'product', 'quantity', 'selling_price', 'total_price')
    list_filter = ('invoice', 'product')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'profile') and request.user.profile.company:
            return qs.filter(invoice__company=request.user.profile.company)
        return qs.none()


# SiteSettings has been replaced by CompanySettings in the accounts app


class InvoiceAdmin(CompanyModelAdmin):
    """Admin interface for Invoice"""
    list_display = ('id', 'company', 'created_by', 'created_at', 'get_subtotal', 'get_tva_amount', 'get_stamp_fee', 'get_total')
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {
            'fields': ('company', 'created_by', 'created_at', 'tva_rate', 'include_stamp_fee', 'custom_total')
        }),
    )


# Register the Invoice model with the custom admin
admin.site.register(models.Invoice, InvoiceAdmin)


@admin.register(models.CalendarEvent)
class CalendarEventAdmin(CompanyModelAdmin):
    list_display = ('title', 'start_date', 'end_date', 'all_day', 'theme', 'company')
    list_filter = ('theme', 'all_day', 'company')
    search_fields = ('title', 'description')
    date_hierarchy = 'start_date'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin interface for Notification"""
    list_display = ('recipient', 'notification_type', 'title', 'created_at', 'is_read')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message')
    date_hierarchy = 'created_at'
    readonly_fields = ('content_type', 'object_id', 'content_object')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'profile') and request.user.profile.company:
            # Filter notifications for users in the same company
            return qs.filter(recipient__profile__company=request.user.profile.company)
        return qs.none()

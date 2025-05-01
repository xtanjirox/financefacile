from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered
from . import models

admin.site.register(models.FinanceEntry)
admin.site.register(models.EntryCategory)
admin.site.register(models.ExpenseCategory)
admin.site.register(models.Expense)
admin.site.register(models.ProductCategory)
admin.site.register(models.Product)
admin.site.register(models.InvoiceItem)


class SiteSettingsAdmin(admin.ModelAdmin):
    """Admin interface for SiteSettings"""
    list_display = ('default_tva_rate', 'stamp_fee')
    
    def has_add_permission(self, request):
        # Only allow adding if no SiteSettings exist yet
        return not models.SiteSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the SiteSettings
        return False


class InvoiceAdmin(admin.ModelAdmin):
    """Admin interface for Invoice"""
    list_display = ('id', 'created_at', 'get_subtotal', 'get_tva_amount', 'get_stamp_fee', 'get_total')
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {
            'fields': ('created_at', 'tva_rate', 'include_stamp_fee', 'custom_total')
        }),
    )


# Register the SiteSettings model with the custom admin
admin.site.register(models.SiteSettings, SiteSettingsAdmin)

# Register the Invoice model with the custom admin
admin.site.register(models.Invoice, InvoiceAdmin)

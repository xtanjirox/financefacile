from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.urls import reverse_lazy
from datetime import datetime


class EntryType(models.IntegerChoices):
    CHARGE = 1, 'DEPENSE'
    REVENUE = 2, 'REVENUE'


class EntryCategory(models.Model):
    category_title = models.CharField(max_length=50)
    finance_entry_type = models.IntegerField(choices=EntryType.choices)

    class Meta:
        db_table = 'entry_category'
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.category_title

    def get_absolute_url(self):
        return reverse_lazy('category-update', kwargs={'pk': self.pk})

    def get_delete_url(self):
        return reverse_lazy('category-delete', kwargs={"pk": self.pk})


class ProductCategory(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Product Category'
        verbose_name_plural = 'Product Categories'

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(ProductCategory, on_delete=models.PROTECT, related_name='products', null=True, blank=True)
    name = models.CharField(max_length=100)
    sku = models.CharField(max_length=50, unique=True)
    quantity = models.PositiveIntegerField(default=0)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    value_current = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    value_1_month = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    value_2_month = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    value_3_month = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'products'
        verbose_name_plural = 'products'

    def __str__(self):
        return f"{self.name} ({self.sku})"

    def get_absolute_url(self):
        return reverse_lazy('product-update', kwargs={'pk': self.pk})

    def get_delete_url(self):
        return reverse_lazy('product-delete', kwargs={"pk": self.pk})

class Invoice(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    # TVA and stamp fee fields
    tva_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        help_text="TVA (VAT) rate in percentage. If left blank, the default site setting will be used."
    )
    include_stamp_fee = models.BooleanField(
        default=True,
        help_text="Whether to include the stamp fee in this invoice."
    )
    custom_total = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        help_text="Manual override for invoice total."
    )

    def __str__(self):
        return f"Invoice #{self.pk}"
    
    def get_tva_rate(self):
        """Get the TVA rate for this invoice, using the default if not specified"""
        if self.tva_rate is not None:
            return self.tva_rate
        return SiteSettings.get_settings().default_tva_rate
    
    def get_stamp_fee(self):
        """Get the stamp fee if it should be included, otherwise 0"""
        if self.include_stamp_fee:
            return SiteSettings.get_settings().stamp_fee
        return 0
    
    def get_subtotal(self):
        """Get the sum of all invoice items before TVA and stamp fee"""
        return sum(item.total_price for item in self.items.all())
    
    def get_tva_amount(self):
        """Calculate the TVA amount based on the subtotal"""
        return self.get_subtotal() * (self.get_tva_rate() / 100)

    def get_total(self):
        """Calculate the total invoice amount including TVA and stamp fee"""
        if self.custom_total is not None:
            return self.custom_total
        
        subtotal = self.get_subtotal()
        tva_amount = self.get_tva_amount()
        stamp_fee = self.get_stamp_fee()
        
        return subtotal + tva_amount + stamp_fee

    def get_absolute_url(self):
        from django.urls import reverse_lazy
        return reverse_lazy('invoice-detail', kwargs={'pk': self.pk})

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True)

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.selling_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product} x {self.quantity} @ {self.selling_price}"

class ExpenseCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = 'Expense Category'
        verbose_name_plural = 'Expense Categories'

    def __str__(self):
        return self.name

class Expense(models.Model):
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT, related_name='expenses')
    date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Expense'
        verbose_name_plural = 'Expenses'
        ordering = ['-date']

    def __str__(self):
        return f"{self.category} - {self.amount} on {self.date}"

    def get_absolute_url(self):
        return reverse_lazy('expense-detail', kwargs={'pk': self.pk})

    def get_delete_url(self):
        return reverse_lazy('expense-delete', kwargs={"pk": self.pk})


class FinanceEntry(models.Model):
    finance_entry_type = models.IntegerField(choices=EntryType.choices)
    entry_category = models.ForeignKey(EntryCategory, on_delete=models.DO_NOTHING)
    entry_value = models.FloatField(default=0)
    entry_label = models.CharField(max_length=20)
    entry_date = models.DateField(default=timezone.now())

    class Meta:
        db_table = 'finance_entries'
        verbose_name_plural = 'entries'

    def __str__(self):
        return str(self.pk) + str(self.entry_label)

    def get_absolute_url(self):
        return reverse_lazy('entry-update', kwargs={'pk': self.pk})

    def get_delete_url(self):
        return reverse_lazy('entry-delete', kwargs={"pk": self.pk})

    @property
    def month_year(self):
        return datetime(self.entry_date.year, self.entry_date.month, 1).strftime("%B%Y")


class SiteSettings(models.Model):
    """Global site settings that can only be modified by administrators"""
    default_tva_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=19.00,
        help_text="Default TVA (VAT) rate in percentage (e.g., 19.00 for 19%)"
    )
    stamp_fee = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        default=1.00,
        help_text="Stamp fee amount to be added to all invoices"
    )
    
    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'
    
    def save(self, *args, **kwargs):
        # Ensure there's only one instance of SiteSettings
        if not self.pk and SiteSettings.objects.exists():
            raise ValidationError('There can only be one SiteSettings instance')
        return super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Get the site settings, creating default ones if none exist"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings


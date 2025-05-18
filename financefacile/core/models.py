from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from accounts.models import Company


def product_image_path(instance, filename):
    return f'products/company_{instance.company.id}/{instance.sku}_{filename}'




# Products

class ProductCategory(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='product_categories', null=True, blank=True)
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Product Category'
        verbose_name_plural = 'Product Categories'
        unique_together = ['company', 'name']

    def __str__(self):
        return self.name
        
    def get_absolute_url(self):
        from django.urls import reverse_lazy
        return reverse_lazy('category-update', kwargs={'pk': self.pk})
        
    def get_delete_url(self):
        from django.urls import reverse_lazy
        return reverse_lazy('category-delete', kwargs={'pk': self.pk})


class Product(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    name = models.CharField(max_length=100)
    sku = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField(default=0)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # selling price
    value_current = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    value_1_month = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    value_2_month = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    value_3_month = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to=product_image_path, null=True, blank=True, help_text="Upload an image of the product")
    created_at = models.DateTimeField(auto_now_add=True)
    is_archived = models.BooleanField(default=False, help_text="Archived products are not shown in active lists but remain available for historical invoices")
    
    def save(self, *args, **kwargs):
        # If no category is specified and the product has a company, assign to 'Uncategorized'
        if not self.category and self.company:
            # Try to find the 'Uncategorized' category for this company
            try:
                uncategorized = ProductCategory.objects.get(company=self.company, name='Uncategorized')
                self.category = uncategorized
            except ProductCategory.DoesNotExist:
                # Create the 'Uncategorized' category if it doesn't exist
                uncategorized = ProductCategory.objects.create(
                    company=self.company,
                    name='Uncategorized'
                )
                self.category = uncategorized
        
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'products'
        verbose_name_plural = 'products'
        unique_together = ['company', 'sku']

    def __str__(self):
        return f"{self.name} ({self.sku})"

    def get_absolute_url(self):
        return reverse_lazy('product-update', kwargs={'pk': self.pk})

    def get_delete_url(self):
        return reverse_lazy('product-delete', kwargs={"pk": self.pk})


# Invoices
class Invoice(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='invoices', null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_invoices')
    created_at = models.DateTimeField(auto_now_add=True)
    # TVA and stamp fee fields
    tva_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        help_text="TVA (VAT) rate in percentage. If left blank, the default company setting will be used."
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
        """Get the TVA rate for this invoice"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Invoice #{self.pk}: get_tva_rate called, self.tva_rate = {self.tva_rate}")
        # Always use the invoice's TVA rate - it should be set during creation
        return self.tva_rate
    
    def get_stamp_fee(self):
        """Get the stamp fee if it should be included, otherwise 0"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Invoice #{self.pk}: get_stamp_fee called, self.include_stamp_fee = {self.include_stamp_fee}")
        
        # Only include stamp fee if the checkbox is checked
        if not self.include_stamp_fee:
            logger.info(f"Invoice #{self.pk}: include_stamp_fee is False, returning 0")
            return 0
            
        # Always use the company settings value for the stamp fee amount
        if self.company and hasattr(self.company, 'settings'):
            fee = self.company.settings.stamp_fee
            logger.info(f"Invoice #{self.pk}: Using company stamp fee: {fee}")
            return fee
        
        # Default fallback if no company settings
        logger.info(f"Invoice #{self.pk}: No company settings, using default stamp fee: 1.0")
        return 1.0  # Default stamp fee if no company settings
    
    def get_subtotal(self):
        """Get the sum of all invoice items before TVA and stamp fee"""
        return sum(item.total_price for item in self.items.all())

    def get_tva_amount(self):
        """Calculate the TVA amount based on the subtotal"""
        return self.get_subtotal() * (self.get_tva_rate() / 100)

    def get_total(self):
        """Calculate the total invoice amount including TVA and stamp fee"""
        from decimal import Decimal
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Invoice #{self.pk}: get_total called")
        
        if self.custom_total is not None:
            logger.info(f"Invoice #{self.pk}: Using custom total: {self.custom_total}")
            return self.custom_total
        
        subtotal = self.get_subtotal()
        tva_amount = self.get_tva_amount()
        stamp_fee = Decimal(str(self.get_stamp_fee()))
        
        logger.info(f"Invoice #{self.pk}: Calculating total: subtotal={subtotal}, tva_amount={tva_amount}, stamp_fee={stamp_fee}")
        total = subtotal + tva_amount + stamp_fee
        logger.info(f"Invoice #{self.pk}: Final total: {total}")
        
        return total

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


# Expenses

class ExpenseCategory(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='expense_categories', null=True, blank=True)
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Expense Category'
        verbose_name_plural = 'Expense Categories'
        unique_together = ['company', 'name']

    def __str__(self):
        return self.name

def expense_attachment_path(instance, filename):
    # File will be uploaded to MEDIA_ROOT/expenses/company_<id>/<date>_<filename>
    return f'expenses/company_{instance.company.id}/{instance.date}_{filename}'

class Expense(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='expenses', null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_expenses')
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT, related_name='expenses')
    date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    attachment = models.FileField(upload_to=expense_attachment_path, null=True, blank=True, help_text="Upload a receipt or invoice for this expense")

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


class InvoiceFees(models.Model):
    invoice_fee_name = models.TextField()
    invoice_fee_value = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = 'InvoiceFees'
        verbose_name_plural = 'InvoiceFees'

    def __str__(self):
        return f"{self.invoice_fee_name}"

    def get_absolute_url(self):
        return reverse_lazy('invoice_fee-detail', kwargs={'pk': self.pk})

    def get_delete_url(self):
        return reverse_lazy('invoice_fee-delete', kwargs={"pk": self.pk})